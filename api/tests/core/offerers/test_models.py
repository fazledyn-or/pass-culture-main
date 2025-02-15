import datetime
from unittest.mock import patch

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from pcapi import settings
from pcapi.connectors import sirene
from pcapi.core.educational import factories as educational_factories
import pcapi.core.finance.factories as finance_factories
import pcapi.core.finance.models as finance_models
from pcapi.core.offerers import factories
from pcapi.core.offerers import models
import pcapi.core.offers.factories as offers_factories
import pcapi.core.offers.models as offers_models
from pcapi.core.testing import assert_num_queries
import pcapi.core.users.factories as users_factories
from pcapi.models import db
from pcapi.models.api_errors import ApiErrors
from pcapi.repository import repository


pytestmark = pytest.mark.usefixtures("db_session")


class VenueModelConstraintsTest:
    def test_virtual_venue_cannot_have_address(self):
        venue = factories.VirtualVenueFactory()

        with pytest.raises(IntegrityError) as err:
            venue.address = "1 test address"
            db.session.add(venue)
            db.session.flush()
        assert "check_is_virtual_xor_has_address" in str(err.value)

    def test_virtual_venue_cannot_have_siret(self):
        venue = factories.VirtualVenueFactory()
        with pytest.raises(IntegrityError) as err:
            venue.siret = "siret"
            db.session.add(venue)
            db.session.flush()
        assert "check_has_siret_xor_comment_xor_isVirtual" in str(err.value)

    def test_non_virtual_with_siret_can_have_null_address(self):
        # The following statement should not fail.
        factories.VenueFactory(siret="siret", address=None)

    def test_non_virtual_with_siret_must_have_postal_code_and_city(self):
        venue = factories.VenueFactory(siret="siret")
        venue.postal_code = None
        venue.city = None
        with pytest.raises(IntegrityError) as err:
            db.session.add(venue)
            db.session.flush()
        assert "check_is_virtual_xor_has_address" in str(err.value)

    def test_non_virtual_without_siret_must_have_full_address(self):
        venue = factories.VenueWithoutSiretFactory()
        venue.address = None
        venue.postal_code = None
        venue.city = None
        with pytest.raises(IntegrityError) as err:
            db.session.add(venue)
            db.session.flush()
        assert "check_is_virtual_xor_has_address" in str(err.value)

    def test_non_virtual_without_siret_must_have_comment(self):
        venue = factories.VenueWithoutSiretFactory()
        with pytest.raises(IntegrityError) as err:
            venue.comment = None
            db.session.add(venue)
            db.session.flush()
        assert "check_has_siret_xor_comment_xor_isVirtual" in str(err.value)

    def test_at_most_one_virtual_venue_per_offerer(self):
        virtual_venue1 = factories.VirtualVenueFactory()
        offerer = virtual_venue1.managingOfferer
        factories.VenueFactory(managingOfferer=offerer)

        # Cannot add new venue (or change the offerer of an existing one).
        virtual_venue2 = factories.VirtualVenueFactory.build(managingOfferer=offerer)
        with pytest.raises(ApiErrors) as err:
            repository.save(virtual_venue2)
        assert err.value.errors["isVirtual"] == ["Un lieu pour les offres numériques existe déjà pour cette structure"]

        # Cannot change isVirtual on an existing one.
        venue3 = factories.VenueFactory(managingOfferer=offerer)
        venue3.isVirtual = True
        venue3.address = venue3.postalCode = venue3.city = venue3.departementCode = None
        venue3.siret = None
        with pytest.raises(ApiErrors) as err:
            repository.save(venue3)
        assert err.value.errors["isVirtual"] == ["Un lieu pour les offres numériques existe déjà pour cette structure"]


class VenueTimezonePropertyTest:
    def test_europe_paris_is_default_timezone(self):
        venue = factories.VenueFactory(postalCode="75000")

        assert venue.timezone == "Europe/Paris"

    def test_return_timezone_given_venue_departement_code(self):
        venue = factories.VenueFactory(postalCode="97300")

        assert venue.timezone == "America/Cayenne"

    def test_return_managing_offerer_timezone_when_venue_is_virtual(self):
        venue = factories.VirtualVenueFactory(managingOfferer__postalCode="97300")

        assert venue.timezone == "America/Cayenne"


class VenueTimezoneSqlQueryTest:
    def test_europe_paris_is_default_timezone(self):
        factories.VenueFactory(postalCode="75000")
        assert models.Venue.query.filter_by(timezone="Europe/Paris").count() == 1

    def test_return_timezone_given_venue_departement_code(self):
        factories.VenueFactory(postalCode="97300")
        assert models.Venue.query.filter_by(timezone="America/Cayenne").count() == 1

    def test_return_managing_offerer_timezone_when_venue_is_virtual(self):
        factories.VirtualVenueFactory(managingOfferer__postalCode="97300")
        assert models.Venue.query.filter_by(timezone="America/Cayenne").count() == 1


class VenueBannerUrlTest:
    def test_can_set_banner_url_when_none(self, db_session):
        expected_banner_url = "http://example.com/banner_url"
        venue = factories.VenueFactory()

        venue.bannerUrl = expected_banner_url
        repository.save(venue)
        db_session.refresh(venue)

        assert venue.bannerUrl == expected_banner_url
        assert venue._bannerUrl == expected_banner_url

    def test_can_update_existing_banner_url(self, db_session):
        expected_banner_url = "http://example.com/banner_url"
        venue = factories.VenueFactory(bannerUrl="http://example.com/legacy_url")

        venue.bannerUrl = expected_banner_url
        repository.save(venue)
        db_session.refresh(venue)

        assert venue.bannerUrl == expected_banner_url
        assert venue._bannerUrl == expected_banner_url

    @pytest.mark.parametrize(
        "venue_type_code", (type_code for type_code, banners in models.VENUE_TYPE_DEFAULT_BANNERS.items() if banners)
    )
    def test_can_get_category_default_banner_url_when_exists(self, venue_type_code):
        venue = factories.VenueFactory(venueTypeCode=venue_type_code)

        banner_base_url, banner_name = venue.bannerUrl.rsplit("/", 1)
        assert banner_name in models.VENUE_TYPE_DEFAULT_BANNERS[venue_type_code]
        assert banner_base_url == f"{settings.OBJECT_STORAGE_URL}/assets/venue_default_images"

    @pytest.mark.parametrize(
        "venue_type_code",
        (type_code for type_code, banners in models.VENUE_TYPE_DEFAULT_BANNERS.items() if not banners),
    )
    def test_cannot_get_category_default_banner_if_not_available(self, venue_type_code):
        venue = factories.VenueFactory(venueTypeCode=venue_type_code)

        assert venue.bannerUrl is None

    def test_can_get_user_defined_banner_if_exists(self):
        expected_banner_url = "http://example.com/banner_url"
        venue = factories.VenueFactory(bannerUrl=expected_banner_url)

        assert venue.bannerUrl == expected_banner_url


class OffererDepartementCodePropertyTest:
    def test_metropole_postal_code(self):
        offerer = factories.OffererFactory.build(postalCode="75000")

        assert offerer.departementCode == "75"

    def test_drom_postal_code(self):
        offerer = factories.OffererFactory.build(postalCode="97300")

        assert offerer.departementCode == "973"


class OffererDepartementCodeSQLExpressionTest:
    def test_metropole_postal_code(self):
        factories.OffererFactory(postalCode="75000")
        assert models.Offerer.query.filter_by(departementCode="75").count() == 1

    def test_drom_postal_code(self):
        factories.OffererFactory(postalCode="97300")
        assert models.Offerer.query.filter_by(departementCode="973").count() == 1


class VenueNApprovedOffersTest:
    def test_venue_n_approved_offers(self):
        venue = factories.VenueFactory()
        for validation_status in offers_models.OfferValidationStatus:
            offers_factories.OfferFactory(venue=venue, validation=validation_status)
        assert venue.nApprovedOffers == 1
        assert venue.has_approved_offers

    def test_venue_n_approved_offers_and_collective_offers(self):
        educational_factories.CollectiveOfferFactory()
        offers_factories.OfferFactory()

        collective_offers = [
            educational_factories.CollectiveOfferFactory(),
            educational_factories.CollectiveOfferFactory(),
        ]
        venue = factories.VenueFactory(collectiveOffers=collective_offers)
        for validation_status in offers_models.OfferValidationStatus:
            offers_factories.OfferFactory(venue=venue, validation=validation_status)
        assert venue.nApprovedOffers == 3
        assert venue.has_approved_offers

    def test_venue_n_approved_offers_zero(self):
        venue = factories.VenueFactory()
        offers_factories.OfferFactory(venue=venue, validation=offers_models.OfferValidationStatus.PENDING)
        educational_factories.CollectiveOfferFactory(venue=venue, validation=offers_models.OfferValidationStatus.DRAFT)
        assert venue.nApprovedOffers == 0
        assert not venue.has_approved_offers


class OffererLegalCategoryTest:
    def test_offerer_legal_category(self):
        offerer = factories.OffererFactory.build()
        assert offerer.legal_category == {
            "code": "1000",
            "label": "Entrepreneur individuel",
        }

    @patch("pcapi.connectors.sirene.get_siren", side_effect=sirene.UnknownEntityException())
    def test_offerer_legal_category_on_error(self, get_siren_mock):
        offerer = factories.OffererFactory.build()
        assert offerer.legal_category == {
            "code": "Donnée indisponible",
            "label": "Donnée indisponible",
        }


def test_save_user_offerer_raise_api_error_when_not_unique(app):
    user = users_factories.ProFactory.build()
    offerer = factories.OffererFactory()
    factories.UserOffererFactory(user=user, offerer=offerer)

    uo2 = factories.UserOffererFactory.build(user=user, offerer=offerer)
    with pytest.raises(ApiErrors) as error:
        repository.save(uo2)

    assert error.value.errors["global"] == ["Une entrée avec cet identifiant existe déjà dans notre base de données"]


class OffererBankInformationTest:
    def test_bic_property_returns_bank_information_bic_when_offerer_has_bank_information(self):
        offerer = factories.OffererFactory()
        finance_factories.BankInformationFactory(offerer=offerer, bic="BDFEFR2LCCB")
        assert offerer.bic == "BDFEFR2LCCB"

    def test_bic_property_returns_none_when_offerer_does_not_have_bank_information(self):
        offerer = factories.OffererFactory()
        assert offerer.bic is None

    def test_iban_property_returns_bank_information_iban_when_offerer_has_bank_information(self):
        offerer = factories.OffererFactory()
        finance_factories.BankInformationFactory(offerer=offerer, iban="FR7630007000111234567890144")
        assert offerer.iban == "FR7630007000111234567890144"

    def test_iban_property_returns_none_when_offerer_does_not_have_bank_information(self):
        offerer = factories.OffererFactory()
        assert offerer.iban is None

    def test_demarchesSimplifieesApplicationId_returns_id_if_status_is_draft(self):
        offerer = factories.OffererFactory()
        finance_factories.BankInformationFactory(
            offerer=offerer,
            applicationId=12345,
            status=finance_models.BankInformationStatus.DRAFT,
        )
        assert offerer.demarchesSimplifieesApplicationId == 12345

    def test_demarchesSimplifieesApplicationId_returns_none_if_status_is_rejected(self):
        offerer = factories.OffererFactory()
        info = finance_factories.BankInformationFactory(
            offerer=offerer,
            applicationId=12345,
            status=finance_models.BankInformationStatus.REJECTED,
        )
        offerer = info.offerer
        assert offerer.demarchesSimplifieesApplicationId is None


class IsValidatedTest:
    def test_is_validated_property(self):
        offerer = factories.OffererFactory()
        factories.NotValidatedUserOffererFactory(offerer=offerer)
        assert offerer.isValidated

    def test_is_validated_property_when_still_offerer_has_validation_token(self):
        offerer = factories.NotValidatedOffererFactory()
        factories.UserOffererFactory(offerer=offerer)
        assert not offerer.isValidated


class HasPendingBankInformationApplicationTest:
    def test_no_application(self):
        venue = factories.VenueFactory()

        assert venue.hasPendingBankInformationApplication is False

    def test_draft_application(self):
        venue = factories.VenueFactory()
        finance_factories.BankInformationFactory(
            venue=venue, status=finance_models.BankInformationStatus.DRAFT, bic=None, iban=None
        )

        assert venue.hasPendingBankInformationApplication is True

    def test_accepted_application(self):
        venue = factories.VenueFactory()
        finance_factories.BankInformationFactory(
            venue=venue,
            status=finance_models.BankInformationStatus.ACCEPTED,
        )

        assert venue.hasPendingBankInformationApplication is False

    def test_rejected_application(self):
        venue = factories.VenueFactory()
        finance_factories.BankInformationFactory(
            venue=venue, status=finance_models.BankInformationStatus.REJECTED, bic=None, iban=None
        )

        assert venue.hasPendingBankInformationApplication is False


class OffererFirstUserPropertyTest:
    def test_first_user_when_none(self):
        offerer = factories.OffererFactory()

        assert offerer.first_user is None

    def test_first_user_when_only_one(self):
        offerer = factories.OffererFactory()
        user_offerer = factories.UserOffererFactory(offerer=offerer)

        assert offerer.first_user == user_offerer.user

    def test_first_user_when_multiple(self):
        offerer = factories.OffererFactory()
        first = factories.UserOffererFactory(offerer=offerer)
        factories.UserOffererFactory.create_batch(3, offerer=offerer)

        assert offerer.first_user == first.user

    def test_first_user_when_only_user_is_rejected(self):
        offerer = factories.OffererFactory()
        factories.RejectedUserOffererFactory(offerer=offerer)

        assert offerer.first_user is None

    def test_first_user_when_only_user_is_deleted(self):
        offerer = factories.OffererFactory()
        factories.DeletedUserOffererFactory(offerer=offerer)

        assert offerer.first_user is None

    def test_first_user_when_first_user_is_rejected_and_other_users(self):
        offerer = factories.OffererFactory()
        rejected_user_offerer = factories.RejectedUserOffererFactory(offerer=offerer)
        factories.UserOffererFactory.create_batch(3, offerer=offerer)

        assert offerer.first_user is not None
        assert offerer.first_user != rejected_user_offerer.user

    def test_first_user_when_first_user_is_deleted_and_other_users(self):
        offerer = factories.OffererFactory()
        deleted_user_offerer = factories.DeletedUserOffererFactory(offerer=offerer)
        factories.UserOffererFactory.create_batch(3, offerer=offerer)

        assert offerer.first_user is not None
        assert offerer.first_user != deleted_user_offerer.user


class VenueDmsAdageStatusTest:
    def test_dms_adage_status_when_no_dms_application(self):
        venue = factories.VenueFactory()

        assert venue.dms_adage_status is None

        # hybrid property: also check SQL expression
        assert db.session.query(models.Venue.dms_adage_status).filter_by(id=venue.id).scalar() is None

    def test_dms_adage_status_when_multiple_dms_application(self):
        venue = factories.VenueFactory()
        educational_factories.CollectiveDmsApplicationFactory.create_batch(
            2, venue=venue, lastChangeDate=datetime.datetime.utcnow() - datetime.timedelta(days=1)
        )
        latest = educational_factories.CollectiveDmsApplicationFactory(
            venue=venue, state="accepte", lastChangeDate=datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        )
        educational_factories.CollectiveDmsApplicationFactory.create_batch(
            2, venue=venue, lastChangeDate=datetime.datetime.utcnow() - datetime.timedelta(days=1)
        )

        assert venue.dms_adage_status == latest.state
        last_collective_dms_application = venue.last_collective_dms_application

        # hybrid property: also check SQL expression
        assert db.session.query(models.Venue.dms_adage_status).filter_by(id=venue.id).scalar() == latest.state
        assert last_collective_dms_application is latest


class CurrentPricingPointTest:
    def _load_venue(self, venue_id) -> models.Venue:
        return (
            models.Venue.query.filter_by(id=venue_id)
            .options(
                sa.orm.joinedload(models.Venue.pricing_point_links).joinedload(
                    models.VenuePricingPointLink.pricingPoint
                )
            )
            .one()
        )

    def test_no_pricing_point(self):
        venue = factories.VenueWithoutSiretFactory()

        venue_with_joinedload = self._load_venue(venue.id)

        with assert_num_queries(0):
            assert venue_with_joinedload.current_pricing_point_link is None
            assert venue_with_joinedload.current_pricing_point is None

    def test_pricing_point(self):
        venue = factories.VenueWithoutSiretFactory()
        now = datetime.datetime.utcnow()
        factories.VenuePricingPointLinkFactory(
            venue=venue,
            pricingPoint=factories.VenueFactory(managingOfferer=venue.managingOfferer, name="former"),
            timespan=[now - datetime.timedelta(days=7), now - datetime.timedelta(days=1)],
        )
        link = factories.VenuePricingPointLinkFactory(
            venue=venue,
            pricingPoint=factories.VenueFactory(managingOfferer=venue.managingOfferer, name="current"),
            timespan=[now - datetime.timedelta(days=1), None],
        )

        venue_with_joinedload = self._load_venue(venue.id)

        with assert_num_queries(0):
            assert venue_with_joinedload.current_pricing_point_link == link
            assert venue_with_joinedload.current_pricing_point is not None
            assert venue_with_joinedload.current_pricing_point.name == "current"


class CurrentReimbursementPointTest:
    def _load_venue(self, venue_id) -> models.Venue:
        return (
            models.Venue.query.filter_by(id=venue_id)
            .options(
                sa.orm.joinedload(models.Venue.reimbursement_point_links).joinedload(
                    models.VenueReimbursementPointLink.reimbursementPoint
                )
            )
            .one()
        )

    def test_no_reimbursement_point(self):
        venue = factories.VenueWithoutSiretFactory()

        venue_with_joinedload = self._load_venue(venue.id)

        with assert_num_queries(0):
            assert venue_with_joinedload.current_reimbursement_point_link is None
            assert venue_with_joinedload.current_reimbursement_point is None

    def test_reimbursement_point(self):
        venue = factories.VenueWithoutSiretFactory()
        now = datetime.datetime.utcnow()
        factories.VenueReimbursementPointLinkFactory(
            venue=venue,
            reimbursementPoint=factories.VenueFactory(managingOfferer=venue.managingOfferer, name="former"),
            timespan=[now - datetime.timedelta(days=7), now - datetime.timedelta(days=1)],
        )
        link = factories.VenueReimbursementPointLinkFactory(
            venue=venue,
            reimbursementPoint=factories.VenueFactory(managingOfferer=venue.managingOfferer, name="current"),
            timespan=[now - datetime.timedelta(days=1), None],
        )

        venue_with_joinedload = self._load_venue(venue.id)

        with assert_num_queries(0):
            assert venue_with_joinedload.current_reimbursement_point_link == link
            assert venue_with_joinedload.current_reimbursement_point is not None
            assert venue_with_joinedload.current_reimbursement_point.name == "current"


class CurrentBankAccountTest:
    def _load_venue(self, venue_id) -> models.Venue:
        return (
            models.Venue.query.filter_by(id=venue_id)
            .options(
                sa.orm.joinedload(models.Venue.bankAccountLinks).joinedload(models.VenueBankAccountLink.bankAccount)
            )
            .one()
        )

    def test_no_bank_account(self):
        venue = factories.VenueWithoutSiretFactory()

        venue_with_joinedload = self._load_venue(venue.id)

        with assert_num_queries(0):
            assert venue_with_joinedload.current_bank_account_link is None

    def test_bank_account_link(self):
        venue = factories.VenueWithoutSiretFactory()
        now = datetime.datetime.utcnow()
        factories.VenueBankAccountLinkFactory(
            venue=venue,
            bankAccount=finance_factories.BankAccountFactory(offererId=venue.managingOffererId, label="former"),
            timespan=[now - datetime.timedelta(days=7), now - datetime.timedelta(days=1)],
        )
        link = factories.VenueBankAccountLinkFactory(
            venue=venue,
            bankAccount=finance_factories.BankAccountFactory(offererId=venue.managingOffererId, label="current"),
            timespan=[now - datetime.timedelta(days=1), None],
        )

        venue_with_joinedload = self._load_venue(venue.id)

        with assert_num_queries(0):
            assert venue_with_joinedload.current_bank_account_link == link
            assert venue_with_joinedload.current_bank_account_link.bankAccount.label == "current"


class VenueBankAccountLinkTest:
    def test_venue_and_bank_account_cant_overlap(self):
        venue = factories.VenueFactory()
        bank_account = finance_factories.BankAccountFactory()

        with pytest.raises(IntegrityError):
            factories.VenueBankAccountLinkFactory(venueId=venue.id, bankAccountId=bank_account.id)
            factories.VenueBankAccountLinkFactory(venueId=venue.id, bankAccountId=bank_account.id)
