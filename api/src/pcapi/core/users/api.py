from dataclasses import asdict
import datetime
from decimal import Decimal
import enum
import logging
import secrets
import typing

from dateutil.relativedelta import relativedelta
from flask import current_app as app
from flask import request
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_refresh_token
from flask_sqlalchemy import BaseQuery
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.orm import Query

from pcapi import settings
from pcapi.connectors import api_adresse
from pcapi.connectors import sirene
from pcapi.core import mails as mails_api
from pcapi.core import token as token_utils
import pcapi.core.bookings.models as bookings_models
import pcapi.core.bookings.repository as bookings_repository
from pcapi.core.external.attributes import api as external_attributes_api
from pcapi.core.external.sendinblue import update_contact_attributes
from pcapi.core.finance import models as finance_models
import pcapi.core.finance.api as finance_api
import pcapi.core.fraud.api as fraud_api
import pcapi.core.fraud.common.models as common_fraud_models
from pcapi.core.geography.repository import get_iris_from_address
import pcapi.core.history.api as history_api
import pcapi.core.history.models as history_models
import pcapi.core.mails.transactional as transactional_mails
import pcapi.core.offerers.api as offerers_api
import pcapi.core.offerers.models as offerers_models
from pcapi.core.permissions import models as perm_models
import pcapi.core.subscription.phone_validation.exceptions as phone_validation_exceptions
import pcapi.core.users.constants as users_constants
import pcapi.core.users.models as users_models
import pcapi.core.users.repository as users_repository
import pcapi.core.users.utils as users_utils
from pcapi.domain.password import random_password
from pcapi.models import db
from pcapi.models import feature
from pcapi.models.api_errors import ApiErrors
from pcapi.models.validation_status_mixin import ValidationStatus
from pcapi.notifications import push as push_api
from pcapi.repository import repository
from pcapi.repository import transaction
from pcapi.routes.serialization.users import ImportUserFromCsvModel
from pcapi.routes.serialization.users import ProUserCreationBodyV2Model
from pcapi.tasks import batch_tasks
from pcapi.utils.clean_accents import clean_accents
import pcapi.utils.date as date_utils
import pcapi.utils.email as email_utils
import pcapi.utils.phone_number as phone_number_utils
import pcapi.utils.postal_code as postal_code_utils
from pcapi.utils.requests import ExternalAPIException

from . import constants
from . import exceptions
from . import models


if typing.TYPE_CHECKING:
    from pcapi.routes.native.v1.serialization import account as account_serialization


class T_UNCHANGED(enum.Enum):
    TOKEN = 0


UNCHANGED = T_UNCHANGED.TOKEN


logger = logging.getLogger(__name__)


def create_reset_password_token(user: models.User, expiration: datetime.datetime | None = None) -> token_utils.Token:
    return token_utils.Token.create(
        token_utils.TokenType.RESET_PASSWORD,
        datetime.datetime.utcnow() - expiration if expiration else constants.RESET_PASSWORD_TOKEN_LIFE_TIME,
        user.id,
    )


def create_phone_validation_token(
    user: models.User,
    phone_number: str,
    expiration: datetime.datetime | None = None,
) -> token_utils.SixDigitsToken:
    if expiration:
        ttl = expiration - datetime.datetime.utcnow()
    else:
        ttl = None
    return token_utils.SixDigitsToken.create(
        type_=token_utils.TokenType.PHONE_VALIDATION, user_id=user.id, ttl=ttl, data={"phone_number": phone_number}
    )


def generate_and_save_token(
    user: models.User,
    token_type: models.TokenType,
    expiration: datetime.datetime | None = None,
    token_value: str | None = None,
    extra_data: models.TokenExtraData | None = None,
) -> models.Token:
    assert token_type.name in models.TokenType.__members__, "Only registered token types are allowed"

    if settings.IS_PERFORMANCE_TESTS:
        token_value = f"performance-tests_{token_type.value}_{user.id}"
    else:
        token_value = token_value or secrets.token_urlsafe(32)

    token = models.Token(
        user=user,
        value=token_value,
        type=token_type,
        expirationDate=expiration,
        extraData=asdict(extra_data) if extra_data else None,  # type: ignore [arg-type]
    )
    repository.save(token)

    return token


def delete_expired_tokens() -> None:
    models.Token.query.filter(
        models.Token.expirationDate < datetime.datetime.utcnow() - users_constants.TOKEN_DELETION_AFTER_EXPIRATION_DELAY
    ).delete()


def delete_all_users_tokens(user: models.User) -> None:
    models.Token.query.filter(models.Token.user == user).delete()
    for token_type in token_utils.TokenType:
        token_utils.Token.delete(token_type, user.id)


def delete_all_users_phone_validation_tokens(user: models.User) -> None:
    token_utils.Token.delete(token_utils.TokenType.PHONE_VALIDATION, user.id)


def create_account(
    email: str,
    password: str | None,
    birthdate: datetime.date,
    marketing_email_subscription: bool = False,
    is_email_validated: bool = False,
    send_activation_mail: bool = True,
    remote_updates: bool = True,
    phone_number: str | None = None,
    apps_flyer_user_id: str | None = None,
    apps_flyer_platform: str | None = None,
    firebase_pseudo_id: str | None = None,
    sso_provider: str | None = None,
    sso_user_id: str | None = None,
) -> models.User:
    email = email_utils.sanitize_email(email)
    if users_repository.find_user_by_email(email):
        raise exceptions.UserAlreadyExistsException()

    user = models.User(
        email=email,
        dateOfBirth=datetime.datetime.combine(birthdate, datetime.datetime.min.time()),
        isEmailValidated=is_email_validated,
        notificationSubscriptions=asdict(
            models.NotificationSubscriptions(marketing_email=marketing_email_subscription)
        ),
        phoneNumber=phone_number,
        lastConnectionDate=datetime.datetime.utcnow(),
    )

    if not user.age or user.age < constants.ACCOUNT_CREATION_MINIMUM_AGE:
        raise exceptions.UnderAgeUserException()

    setup_login(user, password, sso_provider, sso_user_id)

    if user.externalIds is None:
        user.externalIds = {}

    if apps_flyer_user_id and apps_flyer_platform:
        user.externalIds["apps_flyer"] = {"user": apps_flyer_user_id, "platform": apps_flyer_platform.upper()}  # type: ignore [index, call-overload]

    if firebase_pseudo_id:
        user.externalIds["firebase_pseudo_id"] = firebase_pseudo_id  # type: ignore [index, call-overload]

    repository.save(user)
    logger.info("Created user account", extra={"user": user.id})

    delete_all_users_tokens(user)

    if remote_updates:
        external_attributes_api.update_external_user(user)

    if not user.isEmailValidated and send_activation_mail:
        request_email_confirmation(user)

    return user


def setup_login(
    user: models.User, password: str | None, sso_provider: str | None = None, sso_user_id: str | None = None
) -> None:
    if password:
        user.setPassword(password)
        return

    if not sso_provider or not sso_user_id:
        raise exceptions.MissingLoginMethod()

    single_sign_on = users_repository.create_single_sign_on(user, sso_provider, sso_user_id)
    db.session.add(single_sign_on)


def update_user_information(
    user: models.User,
    first_name: str | None = None,
    last_name: str | None = None,
    validated_birth_date: datetime.date | None = None,
    activity: str | None = None,
    address: str | None = None,
    city: str | None = None,
    civility: str | None = None,
    id_piece_number: str | None = None,
    ine_hash: str | None = None,
    married_name: str | None = None,
    postal_code: str | None = None,
    commit: bool = False,
) -> models.User:
    if first_name is not None:
        user.firstName = first_name
    if last_name is not None:
        user.lastName = last_name
    if validated_birth_date is not None:
        user.validatedBirthDate = validated_birth_date
    if activity is not None:
        user.activity = activity
    if address is not None:
        user.address = address
    if city is not None:
        user.city = city
    if civility is not None:
        user.civility = civility
    if id_piece_number is not None:
        if id_piece_number.strip() == "":
            user.idPieceNumber = None
        else:
            user.idPieceNumber = fraud_api.format_id_piece_number(id_piece_number)
    if ine_hash is not None:
        user.ineHash = ine_hash
    if married_name is not None:
        user.married_name = married_name
    if postal_code is not None:
        user.postalCode = postal_code
        user.departementCode = postal_code_utils.PostalCode(postal_code).get_departement_code() if postal_code else None

    user.remove_admin_role()

    db.session.add(user)
    db.session.flush()
    if commit:
        db.session.commit()
    return user


def update_user_information_from_external_source(
    user: models.User,
    data: common_fraud_models.IdentityCheckContent,
    commit: bool = False,
) -> models.User:
    first_name = data.get_first_name()
    last_name = data.get_last_name()
    birth_date = user.validatedBirthDate or data.get_birth_date()

    if not first_name or not last_name or not birth_date:
        raise exceptions.IncompleteDataException()

    return update_user_information(
        user=user,
        first_name=first_name,
        last_name=last_name,
        validated_birth_date=birth_date,
        activity=data.get_activity(),
        address=data.get_address(),
        city=data.get_city(),
        civility=data.get_civility(),
        id_piece_number=data.get_id_piece_number(),
        ine_hash=data.get_ine_hash(),
        married_name=data.get_married_name(),
        postal_code=data.get_postal_code(),
        commit=commit,
    )


def request_email_confirmation(user: models.User) -> None:
    token = token_utils.Token.create(
        token_utils.TokenType.EMAIL_VALIDATION,
        constants.EMAIL_VALIDATION_TOKEN_LIFE_TIME,
        user.id,
    )
    transactional_mails.send_email_confirmation_email(user, token=token)


def _email_validation_resends_key(user: models.User) -> str:
    return f"email_validation_resends_user_{user.id}"


def get_remaining_email_validation_resends(user: models.User) -> int:
    email_validation_resends_count = app.redis_client.get(_email_validation_resends_key(user))

    if email_validation_resends_count:
        return max(settings.MAX_EMAIL_VALIDATION_RESENDS - int(email_validation_resends_count), 0)

    return settings.MAX_EMAIL_VALIDATION_RESENDS


def get_email_validation_resends_limitation_expiration_time(user: models.User) -> datetime.datetime | None:
    ttl = app.redis_client.ttl(_email_validation_resends_key(user))

    if ttl > 0:
        return datetime.datetime.utcnow() + datetime.timedelta(seconds=ttl)

    return None


def check_email_validation_resends_count(user: models.User) -> None:
    """
    Check if the user has reached the maximum number of email validation resends.
    If yes, raise an exception.
    """
    email_validation_resends = app.redis_client.get(_email_validation_resends_key(user))

    if email_validation_resends and int(email_validation_resends) >= settings.MAX_EMAIL_VALIDATION_RESENDS:
        raise exceptions.EmailValidationLimitReached()


def increment_email_validation_resends_count(user: models.User) -> None:
    """
    Increment or initiate the number of resends of the email validation email
    """
    email_validation_resends_key = _email_validation_resends_key(user)
    email_validation_resends = app.redis_client.incr(email_validation_resends_key)

    if email_validation_resends == 1:
        # If the key did not exist, set the expiration time
        app.redis_client.expire(email_validation_resends_key, settings.EMAIL_VALIDATION_RESENDS_TTL)


def request_password_reset(user: models.User | None, reason: constants.SuspensionReason | None = None) -> None:
    if not user:
        return

    token = create_reset_password_token(user)
    is_email_sent = transactional_mails.send_reset_password_email_to_user(token, reason)

    if not is_email_sent:
        logger.error("Email service failure when user requested password reset for email '%s'", user.email)
        raise exceptions.EmailNotSent()


def handle_create_account_with_existing_email(user: models.User) -> None:
    if not user:
        return

    token = create_reset_password_token(user)
    is_email_sent = transactional_mails.send_email_already_exists_email(token)

    if not is_email_sent:
        logger.error("Email service failure when user email already exists in database '%s'", user.email)
        raise exceptions.EmailNotSent()


def check_can_unsuspend(user: models.User) -> None:
    """
    A user can ask for unsuspension if it has been suspended upon his
    own request and if the unsuspension time limit has not been exceeded
    """
    reason = user.suspension_reason
    if not reason:
        raise exceptions.NotSuspended()

    if reason != constants.SuspensionReason.UPON_USER_REQUEST:
        raise exceptions.CantAskForUnsuspension()

    suspension_date = typing.cast(datetime.datetime, user.suspension_date)
    days_delta = datetime.timedelta(days=constants.ACCOUNT_UNSUSPENSION_DELAY)
    if suspension_date.date() + days_delta < datetime.date.today():
        raise exceptions.UnsuspensionTimeLimitExceeded()


def suspend_account(
    user: models.User, reason: constants.SuspensionReason, actor: models.User | None, comment: str | None = None
) -> dict[str, int]:
    """
    Suspend a user's account:
        * mark as inactive;
        * mark as suspended (suspension history);
        * remove its admin role if any;
        * cancel its bookings;

    Notes:
        * `actor` can be None if and only if this function is called
        from an automated task (eg cron).
        * a user who suspends his account should be able to connect to
        the application in order to access to some restricted actions.
    """
    import pcapi.core.bookings.api as bookings_api  # avoid import loop

    with transaction():
        user.isActive = False
        user.remove_admin_role()
        db.session.add(user)
        db.session.add(
            history_api.log_action(
                history_models.ActionType.USER_SUSPENDED,
                author=actor,
                user=user,
                reason=reason.value,
                comment=comment,
                save=False,
            )
        )

        for session in models.UserSession.query.filter_by(userId=user.id):
            db.session.delete(session)

        if user.backoffice_profile:
            user.backoffice_profile.roles = []

    n_bookings = 0

    # Cancel all bookings of the related offerer if the suspended
    # account was the last active offerer's account.
    if reason in (constants.SuspensionReason.FRAUD_SUSPICION, constants.SuspensionReason.BLACKLISTED_DOMAIN_NAME):
        for user_offerer in user.UserOfferers:
            offerer = user_offerer.offerer
            if any(user_of.user.isActive and user_of.user != user for user_of in offerer.UserOfferers):
                continue
            bookings = bookings_repository.find_cancellable_bookings_by_offerer(offerer.id)
            for booking in bookings:
                bookings_api.cancel_booking_for_fraud(booking)
                n_bookings += 1
    elif reason == constants.SuspensionReason.SUSPICIOUS_LOGIN_REPORTED_BY_USER:
        update_user_password(user, random_password())

    n_bookings += _cancel_bookings_of_user_on_requested_account_suspension(user, reason)

    logger.info(
        "Account has been suspended",
        extra={
            "actor": actor.id if actor else None,
            "user": user.id,
            "reason": str(reason),
        },
    )

    return {"cancelled_bookings": n_bookings}


def _cancel_bookings_of_user_on_requested_account_suspension(
    user: users_models.User, reason: constants.SuspensionReason
) -> int:
    import pcapi.core.bookings.api as bookings_api

    bookings_to_cancel = bookings_models.Booking.query.filter(
        bookings_models.Booking.userId == user.id,
        bookings_models.Booking.status == bookings_models.BookingStatus.CONFIRMED,
        sa.or_(
            datetime.datetime.utcnow() < bookings_models.Booking.cancellationLimitDate,
            bookings_models.Booking.cancellationLimitDate.is_(None),
        ),
    ).all()

    cancelled_bookings_count = 0

    for booking in bookings_to_cancel:
        match reason:
            case constants.SuspensionReason.FRAUD_SUSPICION | constants.SuspensionReason.BLACKLISTED_DOMAIN_NAME:
                bookings_api.cancel_booking_for_fraud(booking)
                cancelled_bookings_count += 1

            case constants.SuspensionReason.UPON_USER_REQUEST | constants.SuspensionReason.SUSPICIOUS_LOGIN_REPORTED_BY_USER:
                bookings_api.cancel_booking_on_user_requested_account_suspension(booking)
                cancelled_bookings_count += 1

    return cancelled_bookings_count


def unsuspend_account(
    user: models.User, actor: models.User, comment: str | None = None, send_email: bool = False
) -> None:
    suspension_reason = user.suspension_reason
    user.isActive = True
    action = history_api.log_action(
        history_models.ActionType.USER_UNSUSPENDED, author=actor, user=user, comment=comment, save=False
    )

    repository.save(user, action)

    logger.info(
        "Account has been unsuspended",
        extra={
            "actor": actor.id,
            "user": user.id,
            "send_email": send_email,
        },
    )

    if send_email:
        transactional_mails.send_unsuspension_email(user)

    if suspension_reason == constants.SuspensionReason.SUSPICIOUS_LOGIN_REPORTED_BY_USER:
        request_password_reset(user, constants.SuspensionReason.SUSPICIOUS_LOGIN_REPORTED_BY_USER)


def change_email(
    current_user: models.User,
    new_email: str,
) -> None:
    email_history = models.UserEmailHistory.build_validation(user=current_user, new_email=new_email, by_admin=False)

    try:
        current_user.email = new_email
        repository.save(current_user, email_history)
    except ApiErrors as error:
        # The caller might not want to inform the end client that the
        # email address exists. To do so, raise a specific error and
        # let the caller handle this specific case as needed.
        # Note: email addresses are unique (db constraint)
        if "email" in error.errors:
            raise exceptions.EmailExistsError() from error
        raise

    sessions = models.UserSession.query.filter_by(userId=current_user.id)
    repository.delete(*sessions)

    logger.info("User has changed their email", extra={"user": current_user.id})


def change_pro_user_email(
    current_email: str,
    new_email: str,
    user_id: int,
) -> None:
    current_user = users_repository.find_user_by_email(current_email)
    if not current_user or current_user.id != user_id:
        raise exceptions.UserDoesNotExist()
    change_email(current_user, new_email)


def update_user_password(user: models.User, new_password: str) -> None:
    user.setPassword(new_password)
    repository.save(user)


def update_password_and_external_user(user: users_models.User, new_password: str) -> None:
    user.setPassword(new_password)
    if not user.isEmailValidated:
        user.isEmailValidated = True
        user.validationToken = None
        external_attributes_api.update_external_user(user)
    repository.save(user)


def update_user_info(
    user: users_models.User,
    author: users_models.User,
    cultural_survey_filled_date: datetime.datetime | T_UNCHANGED = UNCHANGED,
    email: str | T_UNCHANGED = UNCHANGED,
    first_name: str | T_UNCHANGED = UNCHANGED,
    last_name: str | T_UNCHANGED = UNCHANGED,
    needs_to_fill_cultural_survey: bool | T_UNCHANGED = UNCHANGED,
    phone_number: str | T_UNCHANGED = UNCHANGED,
    address: str | T_UNCHANGED = UNCHANGED,
    postal_code: str | T_UNCHANGED = UNCHANGED,
    city: str | T_UNCHANGED = UNCHANGED,
    validated_birth_date: datetime.date | T_UNCHANGED = UNCHANGED,
    id_piece_number: str | T_UNCHANGED = UNCHANGED,
) -> history_api.ObjectUpdateSnapshot:
    old_email = None
    snapshot = history_api.ObjectUpdateSnapshot(user, author)

    if cultural_survey_filled_date is not UNCHANGED:
        user.culturalSurveyFilledDate = cultural_survey_filled_date
    if email is not UNCHANGED:
        old_email = user.email
        user.email = email_utils.sanitize_email(email)
    if first_name is not UNCHANGED:
        if user.firstName != first_name:
            snapshot.set("firstName", old=user.firstName, new=first_name)
        user.firstName = first_name
    if last_name is not UNCHANGED:
        if user.lastName != last_name:
            snapshot.set("lastName", old=user.lastName, new=last_name)
        user.lastName = last_name
    if needs_to_fill_cultural_survey is not UNCHANGED:
        user.needsToFillCulturalSurvey = needs_to_fill_cultural_survey
    if phone_number is not UNCHANGED:
        user_phone_number = typing.cast(str, user.phoneNumber)
        if user_phone_number != phone_number:
            snapshot.set("phoneNumber", old=user_phone_number, new=phone_number)
        user.phoneNumber = phone_number  # type: ignore [method-assign]
    if address is not UNCHANGED:
        if address != user.address:
            snapshot.set("address", old=user.address, new=address)
        user.address = address
    if postal_code is not UNCHANGED:
        if user.postalCode != postal_code:
            snapshot.set("postalCode", old=user.postalCode, new=postal_code)
        user.postalCode = postal_code
        user.departementCode = postal_code_utils.PostalCode(postal_code).get_departement_code() if postal_code else None
    if city is not UNCHANGED:
        if city != user.city:
            snapshot.set("city", old=user.city, new=city)
        user.city = city
    if validated_birth_date is not UNCHANGED:
        if validated_birth_date != user.validatedBirthDate:
            snapshot.set("validatedBirthDate", old=user.validatedBirthDate, new=validated_birth_date)
            user.validatedBirthDate = validated_birth_date
            if _has_underage_deposit(user):
                _update_underage_beneficiary_deposit_expiration_date(user)
    if id_piece_number is not UNCHANGED:
        if id_piece_number != user.idPieceNumber:
            snapshot.set("idPieceNumber", old=user.idPieceNumber, new=id_piece_number)
        user.idPieceNumber = id_piece_number

    repository.save(user)

    # TODO(prouzet) even for young users, we should probably remove contact with former email from sendinblue lists
    if old_email and user.has_pro_role:
        external_attributes_api.update_external_pro(old_email)
    external_attributes_api.update_external_user(user)

    return snapshot


def _has_underage_deposit(user: users_models.User) -> bool:
    return user.deposit is not None and user.deposit.type == finance_models.DepositType.GRANT_15_17


def _update_underage_beneficiary_deposit_expiration_date(user: users_models.User) -> None:
    if user.birth_date is None:
        raise ValueError("User has no birth_date")
    if not (user.deposit and user.deposit.expirationDate):
        raise ValueError("Trying to update underage beneficiary deposit expiration date but user has no deposit")

    current_deposit_expiration_datetime = user.deposit.expirationDate
    new_deposit_expiration_datetime = finance_api.compute_underage_deposit_expiration_datetime(user.birth_date)

    if current_deposit_expiration_datetime == new_deposit_expiration_datetime:
        return

    logger.info(
        "Updating deposit expiration date for underage beneficiary %s",
        user.id,
        extra={
            "user": user.id,
            "deposit": user.deposit.id,
            "current_expiration_date": current_deposit_expiration_datetime,
            "new_expiration_date": new_deposit_expiration_datetime,
        },
    )

    if new_deposit_expiration_datetime > datetime.datetime.utcnow():
        user.deposit.expirationDate = new_deposit_expiration_datetime
    else:
        if current_deposit_expiration_datetime < datetime.datetime.utcnow():
            # no need to update the deposit expirationDate because it is already passed
            return
        # Else, reduce to now and not to the theoretical new date in case there are bookings made between these dates
        user.deposit.expirationDate = datetime.datetime.utcnow()

    repository.save(user.deposit)


def add_comment_to_user(user: models.User, author_user: models.User, comment: str) -> None:
    history_api.log_action(history_models.ActionType.COMMENT, author_user, user=user, comment=comment)


def get_domains_credit(
    user: models.User, user_bookings: list[bookings_models.Booking] | None = None
) -> models.DomainsCredit | None:
    if not user.deposit:
        return None

    if user_bookings is None:
        deposit_bookings = bookings_repository.get_bookings_from_deposit(user.deposit.id)
    else:
        deposit_bookings = [
            booking
            for booking in user_bookings
            if booking.depositId == user.deposit.id and booking.status != bookings_models.BookingStatus.CANCELLED
        ]

    domains_credit = models.DomainsCredit(
        all=models.Credit(
            initial=user.deposit.amount,
            remaining=max(user.deposit.amount - sum(booking.total_amount for booking in deposit_bookings), Decimal("0"))
            if user.has_active_deposit
            else Decimal("0"),
        ),
    )
    specific_caps = user.deposit.specific_caps

    if specific_caps.DIGITAL_CAP:
        digital_bookings_total = sum(
            booking.total_amount
            for booking in deposit_bookings
            if specific_caps.digital_cap_applies(booking.stock.offer)
        )
        domains_credit.digital = models.Credit(
            initial=specific_caps.DIGITAL_CAP,
            remaining=(
                min(
                    max(specific_caps.DIGITAL_CAP - digital_bookings_total, Decimal("0")),
                    domains_credit.all.remaining,
                )
            ),
        )

    if specific_caps.PHYSICAL_CAP:
        physical_bookings_total = sum(
            booking.total_amount
            for booking in deposit_bookings
            if specific_caps.physical_cap_applies(booking.stock.offer)
        )
        domains_credit.physical = models.Credit(
            initial=specific_caps.PHYSICAL_CAP,
            remaining=(
                min(
                    max(specific_caps.PHYSICAL_CAP - physical_bookings_total, Decimal("0")),
                    domains_credit.all.remaining,
                )
            ),
        )

    return domains_credit


def import_pro_user_and_offerer_from_csv(pro_user: ImportUserFromCsvModel) -> models.User:
    new_pro_user = create_pro_user(pro_user)

    offerer = _generate_offerer(pro_user.dict(by_alias=True))
    user_offerer = offerers_api.grant_user_offerer_access(offerer, new_pro_user)
    digital_venue = offerers_api.create_digital_venue(offerer)

    new_pro_user = _set_offerer_departement_code(new_pro_user, offerer)

    action = history_api.log_action(
        history_models.ActionType.USER_CREATED, author=new_pro_user, user=new_pro_user, offerer=offerer, save=False
    )

    repository.save(new_pro_user, user_offerer, offerer, digital_venue, action)

    try:
        siren_info = sirene.get_siren(offerer.siren or "")
    except sirene.SireneException as exc:
        logger.info("Could not fetch info from Sirene API", extra={"exc": exc})
        siren_info = None

    offerers_api.auto_tag_new_offerer(offerer, siren_info, new_pro_user)
    extra_data: dict[str, typing.Any] = {}
    if siren_info:
        extra_data = {"sirene_info": dict(siren_info)}

    history_api.log_action(
        history_models.ActionType.OFFERER_NEW,
        new_pro_user,
        user=new_pro_user,
        offerer=offerer,
        **extra_data,
    )

    if not transactional_mails.send_email_validation_to_pro_email(new_pro_user):
        logger.warning(
            "Could not send validation email when creating pro user",
            extra={"user": new_pro_user.id},
        )

    external_attributes_api.update_external_pro(new_pro_user.email)

    return new_pro_user


def create_pro_user_V2(pro_user: ProUserCreationBodyV2Model) -> models.User:
    new_pro_user = create_pro_user(pro_user)

    action = history_api.log_action(
        history_models.ActionType.USER_CREATED, author=new_pro_user, user=new_pro_user, save=False
    )

    repository.save(new_pro_user, action)

    if not transactional_mails.send_email_validation_to_pro_email(new_pro_user):
        logger.warning(
            "Could not send validation email when creating pro user",
            extra={"user": new_pro_user.id},
        )

    external_attributes_api.update_external_pro(new_pro_user.email)
    return new_pro_user


def create_pro_user(pro_user: ImportUserFromCsvModel | ProUserCreationBodyV2Model) -> models.User:
    new_pro_user = models.User(from_dict=pro_user.dict(by_alias=True))
    new_pro_user.email = email_utils.sanitize_email(new_pro_user.email)
    new_pro_user.notificationSubscriptions = asdict(
        models.NotificationSubscriptions(marketing_email=pro_user.contact_ok)
    )
    new_pro_user.add_non_attached_pro_role()
    new_pro_user.remove_admin_role()
    new_pro_user.remove_beneficiary_role()
    new_pro_user.needsToFillCulturalSurvey = False
    new_pro_user.generate_validation_token()

    if hasattr(pro_user, "postal_code") and pro_user.postal_code:
        new_pro_user.departementCode = postal_code_utils.PostalCode(pro_user.postal_code).get_departement_code()

    if settings.IS_INTEGRATION:
        new_pro_user.add_beneficiary_role()
        new_pro_user.validatedBirthDate = new_pro_user.dateOfBirth
        deposit = finance_api.create_deposit(new_pro_user, "integration_signup", models.EligibilityType.AGE18)
        new_pro_user.deposits = [deposit]

    return new_pro_user


def _generate_user_offerer_when_existing_offerer(
    new_user: models.User, offerer: offerers_models.Offerer
) -> offerers_models.UserOfferer:
    user_offerer = offerers_api.grant_user_offerer_access(offerer, new_user)
    if not settings.IS_INTEGRATION:
        user_offerer.validationStatus = ValidationStatus.NEW
    return user_offerer


def _generate_offerer(data: dict) -> offerers_models.Offerer:
    offerer = offerers_models.Offerer()
    offerer.populate_from_dict(data)

    # If offerer was rejected, it appears as deleted from the view. When registering again with the same SIREN, it
    # should look like it was created again, with up-to-date data, and start a new validation process.
    # So in any case, creation date is now:
    offerer.dateCreated = datetime.datetime.utcnow()

    if not settings.IS_INTEGRATION:
        offerer.validationStatus = ValidationStatus.NEW
    else:
        offerer.validationStatus = ValidationStatus.VALIDATED

    return offerer


def _set_offerer_departement_code(new_user: models.User, offerer: offerers_models.Offerer) -> models.User:
    if offerer.postalCode:  # not None, not ""
        new_user.departementCode = postal_code_utils.PostalCode(offerer.postalCode).get_departement_code()
    else:
        new_user.departementCode = None
    return new_user


def set_pro_tuto_as_seen(user: models.User) -> None:
    user.hasSeenProTutorials = True
    repository.save(user)


def set_pro_rgs_as_seen(user: models.User) -> None:
    user.hasSeenProRgs = True
    repository.save(user)


def update_last_connection_date(user: models.User) -> None:
    previous_connection_date = user.lastConnectionDate
    last_connection_date = datetime.datetime.utcnow()

    should_save_last_connection_date = (
        not previous_connection_date or last_connection_date - previous_connection_date > datetime.timedelta(minutes=15)
    )
    should_update_sendinblue_last_connection_date = should_save_last_connection_date and (
        not previous_connection_date
        or last_connection_date.date() - previous_connection_date.date() >= datetime.timedelta(days=1)
    )

    if should_save_last_connection_date:
        user.lastConnectionDate = last_connection_date
        repository.save(user)

    if should_update_sendinblue_last_connection_date:
        external_attributes_api.update_external_user(user, skip_batch=True)


def create_user_access_token(user: models.User) -> str:
    return create_access_token(identity=user.email, additional_claims={"user_claims": {"user_id": user.id}})


def create_user_refresh_token(user: models.User, device_info: "account_serialization.TrustedDevice | None") -> str:
    should_extend_lifetime = (
        feature.FeatureToggle.WIP_ENABLE_TRUSTED_DEVICE.is_active()
        and feature.FeatureToggle.WIP_ENABLE_SUSPICIOUS_EMAIL_SEND.is_active()
        and is_login_device_a_trusted_device(device_info, user)
    )

    if should_extend_lifetime:
        duration = datetime.timedelta(seconds=settings.JWT_REFRESH_TOKEN_EXTENDED_EXPIRES)
    else:
        duration = datetime.timedelta(seconds=settings.JWT_REFRESH_TOKEN_EXPIRES)

    return create_refresh_token(identity=user.email, expires_delta=duration)


def update_notification_subscription(
    user: models.User, subscriptions: "account_serialization.NotificationSubscriptions | None"
) -> None:
    if subscriptions is None:
        return

    user.notificationSubscriptions = {
        "marketing_push": subscriptions.marketing_push,
        "marketing_email": subscriptions.marketing_email,
    }

    repository.save(user)

    if not subscriptions.marketing_push:
        payload = batch_tasks.DeleteBatchUserAttributesRequest(user_id=user.id)
        batch_tasks.delete_user_attributes_task.delay(payload)


def reset_recredit_amount_to_show(user: models.User) -> None:
    user.recreditAmountToShow = None
    repository.save(user)


def get_eligibility_end_datetime(
    date_of_birth: datetime.date | datetime.datetime | None,
) -> datetime.datetime | None:
    if not date_of_birth:
        return None

    return datetime.datetime.combine(date_of_birth, datetime.time(0, 0)) + relativedelta(
        years=constants.ELIGIBILITY_AGE_18 + 1, hour=11
    )


def get_eligibility_start_datetime(
    date_of_birth: datetime.date | datetime.datetime | None,
) -> datetime.datetime | None:
    if not date_of_birth:
        return None

    date_of_birth = datetime.datetime.combine(date_of_birth, datetime.time(0, 0))
    fifteenth_birthday = date_of_birth + relativedelta(years=constants.ELIGIBILITY_UNDERAGE_RANGE[0])

    return fifteenth_birthday


def get_eligibility_at_date(
    date_of_birth: datetime.date | None,
    specified_datetime: datetime.datetime,
) -> models.EligibilityType | None:
    eligibility_start = get_eligibility_start_datetime(date_of_birth)
    eligibility_end = get_eligibility_end_datetime(date_of_birth)

    if not date_of_birth or not (eligibility_start <= specified_datetime < eligibility_end):  # type: ignore [operator]
        return None

    age = users_utils.get_age_at_date(date_of_birth, specified_datetime)
    if not age:
        return None

    if age in constants.ELIGIBILITY_UNDERAGE_RANGE:
        return models.EligibilityType.UNDERAGE
    # If the user is older than 18 in UTC timezone, we consider them eligible until they reach eligibility_end
    if constants.ELIGIBILITY_AGE_18 <= age and specified_datetime < eligibility_end:  # type: ignore [operator]
        return models.EligibilityType.AGE18

    return None


def is_eligible_for_beneficiary_upgrade(user: models.User, eligibility: models.EligibilityType | None) -> bool:
    return (eligibility == models.EligibilityType.UNDERAGE and not user.is_beneficiary) or (
        eligibility == models.EligibilityType.AGE18 and not user.has_beneficiary_role
    )


def is_user_age_compatible_with_eligibility(user_age: int | None, eligibility: models.EligibilityType | None) -> bool:
    if eligibility == models.EligibilityType.UNDERAGE:
        return user_age in constants.ELIGIBILITY_UNDERAGE_RANGE
    if eligibility == models.EligibilityType.AGE18:
        return user_age is not None and user_age >= constants.ELIGIBILITY_AGE_18
    return False


def _filter_user_accounts(accounts: BaseQuery, search_term: str) -> BaseQuery:
    filters = []
    name_term = None

    if not search_term:
        return accounts.filter(False)

    term_filters: list[sa.sql.ColumnElement] = []

    # phone number
    try:
        parsed_phone_number = phone_number_utils.parse_phone_number(search_term)
        term_as_phone_number = phone_number_utils.get_formatted_phone_number(parsed_phone_number)
    except phone_validation_exceptions.InvalidPhoneNumber:
        pass  # term can't be a phone number
    else:
        term_filters.append(models.User.phoneNumber == term_as_phone_number)  # type: ignore [arg-type]

    # numeric
    if search_term.isnumeric():
        term_filters.append(models.User.id == int(search_term))

    # email
    sanitized_term = email_utils.sanitize_email(search_term)

    if email_utils.is_valid_email(sanitized_term):
        term_filters.append(models.User.email == sanitized_term)
    elif email_utils.is_valid_email_domain(sanitized_term):
        # search for all emails @domain.ext
        term_filters.append(models.User.email.like(f"%{sanitized_term}"))

    if not term_filters:
        name_term = search_term
        for name in name_term.split():
            term_filters.append(
                sa.func.unaccent(sa.func.concat(models.User.firstName, " ", models.User.lastName)).ilike(
                    f"%{clean_accents(name)}%"
                )
            )
        filters.append(sa.and_(*term_filters) if len(term_filters) > 1 else term_filters[0])

    else:
        filters.append(sa.or_(*term_filters) if len(term_filters) > 1 else term_filters[0])

    # each result must match all terms in any column
    accounts = accounts.filter(*filters).from_self()

    if name_term:
        name_term = name_term.lower()
        accounts = accounts.order_by(
            sa.func.levenshtein(
                sa.func.lower(sa.func.concat(models.User.firstName, " ", models.User.lastName)), name_term
            )
        )

    accounts = accounts.order_by(models.User.id)

    return accounts


def search_public_account(search_query: str) -> BaseQuery:
    public_accounts = get_public_account_base_query()

    return _filter_user_accounts(public_accounts, search_query)


def search_public_account_in_history_email(search_query: str) -> BaseQuery:
    if not email_utils.is_valid_email_or_email_domain(email_utils.sanitize_email(search_query)):
        raise ValueError(f"Unsupported email search on invalid email or email domain : {search_query}")

    accounts = get_public_account_base_query()

    if not search_query:
        return accounts.filter(False)

    # email
    sanitized_term = email_utils.sanitize_email(search_query)

    if email_utils.is_valid_email(sanitized_term):
        accounts = accounts.join(models.UserEmailHistory)

        # including old emails: look for validated email updates inside user_email_history
        accounts = accounts.filter(
            models.UserEmailHistory.oldEmail == sanitized_term,
            models.UserEmailHistory.eventType.in_(
                {
                    models.EmailHistoryEventTypeEnum.VALIDATION,
                    models.EmailHistoryEventTypeEnum.ADMIN_VALIDATION,
                    models.EmailHistoryEventTypeEnum.ADMIN_UPDATE,
                }
            ),
        ).from_self()
    elif email_utils.is_valid_email_domain(sanitized_term):
        accounts = accounts.join(models.UserEmailHistory)

        # including old emails: look for validated email updates inside user_email_history
        accounts = accounts.filter(
            sa.or_(
                models.User.email.like(f"%{sanitized_term}"),
                sa.and_(
                    models.UserEmailHistory.oldDomainEmail == sanitized_term[1:],
                    models.UserEmailHistory.eventType.in_(
                        {
                            models.EmailHistoryEventTypeEnum.VALIDATION,
                            models.EmailHistoryEventTypeEnum.ADMIN_VALIDATION,
                        }
                    ),
                ),
            )
        ).from_self()

    return accounts.order_by(models.User.id)


def get_public_account_base_query() -> BaseQuery:
    # There is no fully reliable condition to be sure that a user account is used as a public account (vs only pro).
    # In Flask-Admin backoffice, the difference was made from user_offerer table, which turns the user into a "pro"
    # account ; the same filter is kept here.
    # However, some young users, including beneficiaries, work for organizations and are associated with offerers
    # using the same email as their personal account. So let's include "pro" users who are beneficiaries (doesn't
    # include those who are only in the subscription process).
    public_accounts = (
        models.User.query.outerjoin(users_models.User.backoffice_profile)
        .filter(
            sa.or_(
                sa.and_(
                    models.User.has_pro_role.is_(False),  # type: ignore [attr-defined]
                    models.User.has_non_attached_pro_role.is_(False),  # type: ignore [attr-defined]
                    perm_models.BackOfficeUserProfile.id.is_(None),
                ),
                models.User.is_beneficiary.is_(True),  # type: ignore [attr-defined]
            ),
        )
        .distinct(models.User.id)
    )
    return public_accounts


# TODO (prouzet, 2023-11-02) This function should be moved in backoffice and use common _join_suspension_history()
def search_pro_account(search_query: str, *_: typing.Any) -> BaseQuery:
    pro_accounts = models.User.query.filter(
        models.User.has_non_attached_pro_role.is_(True) | models.User.has_pro_role.is_(True)  # type: ignore [attr-defined]
    )

    return (
        _filter_user_accounts(pro_accounts, search_query)
        .outerjoin(
            # Join only suspension actions to limit the number of fetched rows
            history_models.ActionHistory,
            sa.and_(
                history_models.ActionHistory.userId == models.User.id,
                history_models.ActionHistory.actionType.in_(
                    [history_models.ActionType.USER_SUSPENDED, history_models.ActionType.USER_UNSUSPENDED]
                ),
            ),
        )
        .options(
            sa.orm.joinedload(users_models.User.UserOfferers).load_only(offerers_models.UserOfferer.validationStatus),
            sa.orm.contains_eager(users_models.User.action_history),
        )
    )


def get_pro_account_base_query(pro_id: int) -> BaseQuery:
    return models.User.query.filter(
        models.User.id == pro_id,
        sa.or_(
            models.User.has_non_attached_pro_role.is_(True),  # type: ignore [attr-defined]
            models.User.has_pro_role.is_(True),  # type: ignore [attr-defined]
        ),
    )


def search_backoffice_accounts(search_query: str) -> BaseQuery:
    bo_accounts = models.User.query.join(users_models.User.backoffice_profile)

    if not search_query:
        return bo_accounts

    return _filter_user_accounts(bo_accounts, search_query)


def validate_pro_user_email(user: users_models.User, author_user: users_models.User | None = None) -> None:
    user.validationToken = None
    user.isEmailValidated = True
    if author_user:
        action = history_api.log_action(
            history_models.ActionType.USER_EMAIL_VALIDATED,
            author=author_user,
            user=user,
            save=False,
        )
        repository.save(user, action)
    else:
        repository.save(user)

    offerers_api.accept_offerer_invitation_if_exists(user)


def save_firebase_flags(user: models.User, firebase_value: dict) -> None:
    user_pro_flags = users_models.UserProFlags.query.filter(users_models.UserProFlags.user == user).one_or_none()
    if user_pro_flags:
        if user.pro_flags.firebase and user.pro_flags.firebase != firebase_value:
            logger.warning("%s now has different Firebase flags than before", user)
        user.pro_flags.firebase = firebase_value
    else:
        user_pro_flags = users_models.UserProFlags(user=user, firebase=firebase_value)
    repository.save(user_pro_flags)


def save_flags(user: models.User, flags: dict) -> None:
    for flag, value in flags.items():
        match flag:
            case "firebase":
                save_firebase_flags(user, value)
            case _:
                raise ValueError()


def save_trusted_device(device_info: "account_serialization.TrustedDevice", user: models.User) -> None:
    if not device_info.device_id:
        logger.info(
            "Invalid deviceId was provided for trusted device",
            extra={
                "deviceId": device_info.device_id,
                "os": device_info.os,
                "source": device_info.source,
            },
        )
        return

    trusted_device = users_models.TrustedDevice(
        deviceId=device_info.device_id,
        os=device_info.os,
        source=device_info.source,
        user=user,
    )
    repository.save(trusted_device)


def update_login_device_history(
    device_info: "account_serialization.TrustedDevice", user: models.User
) -> users_models.LoginDeviceHistory | None:
    if not device_info.device_id:
        logger.info(
            "Invalid deviceId was provided for login device",
            extra={
                "deviceId": device_info.device_id,
                "os": device_info.os,
                "source": device_info.source,
            },
        )
        return None

    location = users_utils.format_login_location(request.headers.get("X-Country"), request.headers.get("X-City"))

    login_device = users_models.LoginDeviceHistory(
        deviceId=device_info.device_id,
        os=device_info.os,
        source=device_info.source,
        user=user,
        location=location,
    )
    repository.save(login_device)

    return login_device


def should_save_login_device_as_trusted_device(
    device_info: "account_serialization.TrustedDevice", user: models.User
) -> bool:
    if not device_info.device_id:
        return False

    if any(device.deviceId == device_info.device_id for device in user.trusted_devices):
        return False

    return db.session.query(
        users_models.LoginDeviceHistory.query.with_entities(users_models.LoginDeviceHistory.deviceId)
        .filter(users_models.LoginDeviceHistory.userId == user.id)
        .filter(users_models.LoginDeviceHistory.deviceId == device_info.device_id)
        .exists()
    ).scalar()


def is_login_device_a_trusted_device(
    device_info: "account_serialization.TrustedDevice | None", user: models.User
) -> bool:
    if device_info is None or not device_info.device_id:
        return False

    if any(device.deviceId == device_info.device_id for device in user.trusted_devices):
        return True

    return False


def get_recent_suspicious_logins(user: users_models.User) -> list[users_models.LoginDeviceHistory]:
    yesterday = datetime.datetime.utcnow() - relativedelta(hours=24)
    recent_logins = users_models.LoginDeviceHistory.query.filter(
        users_models.LoginDeviceHistory.user == user,
        users_models.LoginDeviceHistory.dateCreated >= yesterday,
    ).all()
    recent_trusted_devices = users_models.TrustedDevice.query.filter(
        users_models.TrustedDevice.dateCreated >= yesterday,
    ).all()
    user_trusted_device_ids = [device.deviceId for device in user.trusted_devices]

    recent_suspicious_logins = []
    for recent_login in recent_logins:
        if recent_login.deviceId not in user_trusted_device_ids:
            recent_suspicious_logins.append(recent_login)
            continue

        was_device_trusted_after_suspicious_login = any(
            trusted_device.deviceId == recent_login.deviceId and trusted_device.dateCreated > recent_login.dateCreated
            for trusted_device in recent_trusted_devices
        )
        if was_device_trusted_after_suspicious_login:
            recent_suspicious_logins.append(recent_login)

    return recent_suspicious_logins


def create_suspicious_login_email_token(
    login_info: users_models.LoginDeviceHistory | None, user_id: int
) -> token_utils.Token:
    if login_info is None:
        return token_utils.Token.create(
            token_utils.TokenType.SUSPENSION_SUSPICIOUS_LOGIN,
            users_constants.SUSPICIOUS_LOGIN_EMAIL_TOKEN_LIFE_TIME,
            user_id,
            {"dateCreated": datetime.datetime.utcnow().strftime(date_utils.DATE_ISO_FORMAT)},
        )

    passed_ttl = datetime.datetime.utcnow() - login_info.dateCreated
    remaining_ttl = users_constants.SUSPICIOUS_LOGIN_EMAIL_TOKEN_LIFE_TIME - passed_ttl

    return token_utils.Token.create(
        token_utils.TokenType.SUSPENSION_SUSPICIOUS_LOGIN,
        remaining_ttl,
        user_id,
        {
            "dateCreated": login_info.dateCreated.strftime(date_utils.DATE_ISO_FORMAT),
            "location": login_info.location,
            "os": login_info.os,
            "source": login_info.source,
        },
    )


def save_device_info_and_notify_user(
    user: models.User, device_info: "account_serialization.TrustedDevice | None"
) -> None:
    login_history = None
    if device_info is not None:
        if should_save_login_device_as_trusted_device(device_info, user):
            save_trusted_device(device_info, user)

        login_history = update_login_device_history(device_info, user)

    should_send_suspicious_login_email = (
        (user.is_active or user.is_account_suspended_upon_user_request)
        and not is_login_device_a_trusted_device(device_info, user)
        and feature.FeatureToggle.WIP_ENABLE_SUSPICIOUS_EMAIL_SEND.is_active()
        and len(get_recent_suspicious_logins(user)) <= constants.MAX_SUSPICIOUS_LOGIN_EMAILS
    )

    if should_send_suspicious_login_email:
        account_suspension_token = create_suspicious_login_email_token(login_history, user.id)
        reset_password_token = create_reset_password_token(user)
        transactional_mails.send_suspicious_login_email(
            user, login_history, account_suspension_token, reset_password_token
        )


def delete_old_trusted_devices() -> None:
    five_years_ago = datetime.datetime.utcnow() - relativedelta(years=5)

    users_models.TrustedDevice.query.filter(users_models.TrustedDevice.dateCreated <= five_years_ago).delete()
    db.session.commit()


def delete_old_login_device_history() -> None:
    thirteen_months_ago = datetime.datetime.utcnow() - relativedelta(months=13)

    users_models.LoginDeviceHistory.query.filter(
        users_models.LoginDeviceHistory.dateCreated <= thirteen_months_ago
    ).delete()
    db.session.commit()


def _get_users_with_suspended_account() -> Query:
    # distinct keeps the first row if duplicates are found. Since rows
    # are ordered by userId and eventDate, this query will fetch the
    # latest event for each userId.
    return (
        users_models.User.query.distinct(history_models.ActionHistory.userId)
        .join(users_models.User.action_history)
        .filter(
            history_models.ActionHistory.actionType == history_models.ActionType.USER_SUSPENDED,
            users_models.User.isActive.is_(False),
        )
        .order_by(history_models.ActionHistory.userId, history_models.ActionHistory.actionDate.desc())
    )


def _get_users_with_suspended_account_to_notify(expiration_delta_in_days: int) -> Query:
    start = datetime.date.today() - datetime.timedelta(days=expiration_delta_in_days)
    user_ids_and_latest_action = (
        _get_users_with_suspended_account()
        .with_entities(
            users_models.User.id,
            history_models.ActionHistory.actionDate,
            history_models.ActionHistory.extraData["reason"].astext.label("reason"),
        )
        .subquery()
    )
    return (
        users_models.User.query.join(
            user_ids_and_latest_action, user_ids_and_latest_action.c.id == users_models.User.id
        )
        .filter(
            user_ids_and_latest_action.c.actionDate - start >= datetime.timedelta(days=0),
            user_ids_and_latest_action.c.actionDate - start < datetime.timedelta(days=1),
            user_ids_and_latest_action.c.reason == constants.SuspensionReason.UPON_USER_REQUEST.value,
        )
        .with_entities(users_models.User)
    )


def get_suspended_upon_user_request_accounts_since(expiration_delta_in_days: int) -> Query:
    start = datetime.date.today() - datetime.timedelta(days=expiration_delta_in_days)
    user_ids_and_latest_action = (
        _get_users_with_suspended_account()
        .with_entities(
            users_models.User.id,
            history_models.ActionHistory.actionDate,
            history_models.ActionHistory.extraData["reason"].astext.label("reason"),
        )
        .subquery()
    )
    return (
        users_models.User.query.join(
            user_ids_and_latest_action, user_ids_and_latest_action.c.id == users_models.User.id
        )
        .filter(
            user_ids_and_latest_action.c.actionDate <= start,
            user_ids_and_latest_action.c.reason == constants.SuspensionReason.UPON_USER_REQUEST.value,
        )
        .with_entities(users_models.User)
    )


def notify_users_before_deletion_of_suspended_account() -> None:
    expiration_delta_in_days = settings.DELETE_SUSPENDED_ACCOUNTS_SINCE - settings.NOTIFY_X_DAYS_BEFORE_DELETION
    accounts_to_notify = _get_users_with_suspended_account_to_notify(expiration_delta_in_days)
    for account in accounts_to_notify:
        if not transactional_mails.send_email_before_deletion_of_suspended_account(account):
            logger.warning(
                "Could not send email before deletion of suspended account",
                extra={"user": account.id},
            )


def anonymize_user(user: users_models.User, *, force: bool = False) -> None:
    """
    Anonymize the given User. If force is True, the function will anonymize the user even if they have an address and
    we cannot find an iris for it.
    """
    iris = None
    if user.address:
        try:
            iris = get_iris_from_address(address=user.address, postcode=user.postalCode)
        except (api_adresse.AdresseApiException, api_adresse.InvalidFormatException) as exc:
            logger.exception("Could not anonymize user", extra={"user_id": user.id, "exc": str(exc)})
            return

        if not iris and not force:
            return

    try:
        push_api.delete_user_attributes(user_id=user.id, can_be_asynchronously_retried=True)
    except ExternalAPIException as exc:
        # If is_retryable it is a real error. If this flag is False then it means the email is unknown for brevo.
        if exc.is_retryable:
            logger.exception("Could not anonymize user", extra={"user_id": user.id, "exc": str(exc)})
            return
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("Could not anonymize user", extra={"user_id": user.id, "exc": str(exc)})
        return

    for beneficiary_fraud_check in user.beneficiaryFraudChecks:
        beneficiary_fraud_check.resultContent = None
        beneficiary_fraud_check.reason = "Anonymized"
        beneficiary_fraud_check.dateCreated = beneficiary_fraud_check.dateCreated.replace(day=1, month=1)
        beneficiary_fraud_check.updatedAt = beneficiary_fraud_check.updatedAt.replace(day=1, month=1)

    for beneficiary_fraud_review in user.beneficiaryFraudReviews:
        beneficiary_fraud_review.reason = "Anonymized"
        beneficiary_fraud_review.dateReviewed = beneficiary_fraud_review.dateReviewed.replace(day=1, month=1)

    for deposit in user.deposits:
        deposit.source = "Anonymized"

    user.password = b"Anonymized"
    user.firstName = f"Anonymous_{user.id}"
    user.lastName = f"Anonymous_{user.id}"
    user.married_name = None
    user.postalCode = None
    user.phoneNumber = None  # type: ignore [method-assign]
    user.dateOfBirth = user.dateOfBirth.replace(day=1, month=1) if user.dateOfBirth else None
    user.address = None
    user.city = None
    user.externalIds = []
    user.idPieceNumber = None
    user.user_email_history = []
    user.isActive = False
    user.irisFrance = iris
    user.validatedBirthDate = user.validatedBirthDate.replace(day=1, month=1) if user.validatedBirthDate else None

    external_email_anonymized = _anonymize_external_user_email(user)

    users_models.TrustedDevice.query.filter(users_models.TrustedDevice.userId == user.id).delete()
    users_models.LoginDeviceHistory.query.filter(users_models.LoginDeviceHistory.userId == user.id).delete()
    history_models.ActionHistory.query.filter(
        history_models.ActionHistory.userId == user.id,
        history_models.ActionHistory.offererId.is_(None),
    ).delete()

    if external_email_anonymized:
        user.replace_roles_by_anonymized_role()
        user.email = f"anonymous_{user.id}@anonymized.passculture"
        db.session.add(
            history_models.ActionHistory(
                actionType=history_models.ActionType.USER_ANONYMIZED,
                userId=user.id,
            )
        )
    return


def _anonymize_external_user_email(user: users_models.User) -> bool:
    # check if this email is used in booking_email (it should not be)
    is_email_used = (
        db.session.query(
            offerers_models.Venue.id,
        )
        .filter(
            offerers_models.Venue.bookingEmail == user.email,
        )
        .limit(1)
        .count()
    )

    # clean personal data on email partner's side
    try:
        if is_email_used:
            attributes = external_attributes_api.get_anonymized_attributes(user)
            update_contact_attributes(user.email, attributes, asynchronous=False)
        else:
            mails_api.delete_contact(user.email)
    except ExternalAPIException as exc:
        # If is_retryable it is a real error. If this flag is False then it means the email is unknown for brevo.
        if exc.is_retryable:
            logger.exception("Could not anonymize user", extra={"user_id": user.id, "exc": str(exc)})
            return False
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("Could not anonymize user", extra={"user_id": user.id, "exc": str(exc)})
        return False

    return True


def anonymize_non_pro_non_beneficiary_users(*, force: bool = False) -> None:
    """
    Anonymize user accounts that have never been beneficiary (no deposits), are not pro (no pro role) and which have
    not connected for at least 3 years.
    """
    users = (
        users_models.User.query.outerjoin(
            finance_models.Deposit,
            users_models.User.deposits,
        )
        .filter(
            ~users_models.User.email.like("%@passculture.app"),  # people who work or worked in the company
            func.array_length(users_models.User.roles, 1).is_(None),  # no role, not already anonymized
            finance_models.Deposit.userId.is_(None),  # no deposit
            users_models.User.lastConnectionDate < datetime.datetime.utcnow() - relativedelta(years=3),
        )
        .all()
    )
    for user in users:
        anonymize_user(user, force=force)
    db.session.commit()


def anonymize_beneficiary_users(*, force: bool = False) -> None:
    """
    Anonymize user accounts that have been beneficiaries which have not connected for at least 3 years, and
    whose deposit has been expired for at least 5 years.
    """
    users = (
        users_models.User.query.outerjoin(
            finance_models.Deposit,
            users_models.User.deposits,
        )
        .filter(
            users_models.User.is_beneficiary.is_(True),  # type: ignore [attr-defined]
            sa.and_(
                users_models.User.lastConnectionDate < datetime.datetime.utcnow() - relativedelta(years=3),
                finance_models.Deposit.expirationDate < datetime.datetime.utcnow() - relativedelta(years=5),
            ),
        )
        .all()
    )
    for user in users:
        anonymize_user(user, force=force)
    db.session.commit()


def anonymize_user_deposits() -> None:
    """
    Anonymize deposits that have been expired for at least 10 years.
    """
    deposits_query = finance_models.Deposit.query.filter(
        finance_models.Deposit.expirationDate < datetime.datetime.utcnow() - relativedelta(years=10),
        ~sa.and_(  # ignore already anonymized deposits
            sa.func.extract("month", finance_models.Deposit.expirationDate) == 1,
            sa.func.extract("day", finance_models.Deposit.expirationDate) == 1,
            sa.func.extract("month", finance_models.Deposit.dateCreated) == 1,
            sa.func.extract("day", finance_models.Deposit.dateCreated) == 1,
        ),
    )
    deposits_query.update(
        {
            "expirationDate": sa.func.date_trunc("year", finance_models.Deposit.expirationDate),
            "dateCreated": sa.func.date_trunc("year", finance_models.Deposit.dateCreated),
        },
        synchronize_session=False,
    )

    db.session.commit()
