from datetime import datetime
from datetime import timedelta
import hashlib
import logging

from pcapi.core.educational.constants import INSTITUTION_TYPES


logger = logging.getLogger(__name__)


def compute_educational_booking_cancellation_limit_date(
    event_beginning: datetime, booking_creation_date: datetime
) -> datetime:
    fifteen_days_before_event = event_beginning - timedelta(days=15)
    return max(fifteen_days_before_event, booking_creation_date)


def get_institution_type_and_name(institution_title: str) -> tuple[str, str]:
    short_type = ""
    for index in INSTITUTION_TYPES:
        if institution_title.strip().startswith(f"{index} ") or institution_title == index:
            short_type = index
            break

    name = institution_title.replace(index, "", 1).strip()
    long_type = INSTITUTION_TYPES.get(short_type, "").strip()
    return long_type, name


def get_hashed_user_id(email: str) -> str:
    return hashlib.sha256(email.encode("utf-8")).hexdigest()


def log_information_for_data_purpose(
    event_name: str,
    user_email: str | None = None,
    extra_data: dict[str, str | int] | None = None,
) -> None:
    if extra_data is None:
        extra_data = {}

    if user_email is not None:
        user_id = get_hashed_user_id(user_email)
        extra_data["userId"] = user_id

    logger.info(  # type: ignore [call-arg]
        event_name,
        extra={"analyticsSource": "adage", **extra_data},
        technical_message_id="collective_analytics_event",
    )
