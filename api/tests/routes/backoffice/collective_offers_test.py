from dataclasses import asdict
import datetime
from decimal import Decimal

from flask import url_for
import pytest

from pcapi.core.categories import categories
from pcapi.core.categories import subcategories_v2 as subcategories
from pcapi.core.educational import factories as educational_factories
from pcapi.core.educational import models as educational_models
from pcapi.core.finance import api as finance_api
from pcapi.core.finance import conf as finance_conf
from pcapi.core.finance import factories as finance_factories
from pcapi.core.finance import models as finance_models
from pcapi.core.mails import testing as mails_testing
from pcapi.core.mails.transactional.sendinblue_template_ids import TransactionalEmail
from pcapi.core.offerers import factories as offerers_factories
from pcapi.core.offers import factories as offers_factories
from pcapi.core.offers import models as offers_models
from pcapi.core.permissions import models as perm_models
from pcapi.core.testing import assert_num_queries
from pcapi.models import db
from pcapi.models.offer_mixin import OfferValidationStatus
from pcapi.models.offer_mixin import OfferValidationType
from pcapi.routes.backoffice.filters import format_date

from .helpers import html_parser
from .helpers.get import GetEndpointHelper
from .helpers.post import PostEndpointHelper


pytestmark = [
    pytest.mark.usefixtures("db_session"),
    pytest.mark.backoffice,
]


@pytest.fixture(scope="function", name="collective_offers")
def collective_offers_fixture() -> tuple:
    collective_offer_1 = educational_factories.CollectiveStockFactory(
        beginningDatetime=datetime.date.today(),
        collectiveOffer__subcategoryId=subcategories.ATELIER_PRATIQUE_ART.id,
    ).collectiveOffer
    collective_offer_2 = educational_factories.CollectiveStockFactory(
        beginningDatetime=datetime.date.today(),
        collectiveOffer__name="A Very Specific Name",
        collectiveOffer__subcategoryId=subcategories.EVENEMENT_CINE.id,
        collectiveOffer__formats=[subcategories.EacFormat.PROJECTION_AUDIOVISUELLE],
    ).collectiveOffer
    collective_offer_3 = educational_factories.CollectiveStockFactory(
        beginningDatetime=datetime.date.today(),
        collectiveOffer__dateCreated=datetime.date.today() - datetime.timedelta(days=2),
        collectiveOffer__name="A Very Specific Name That Is Longer",
        collectiveOffer__subcategoryId=subcategories.FESTIVAL_CINE.id,
        collectiveOffer__formats=[
            subcategories.EacFormat.FESTIVAL_SALON_CONGRES,
            subcategories.EacFormat.PROJECTION_AUDIOVISUELLE,
        ],
        collectiveOffer__validation=offers_models.OfferValidationStatus.REJECTED,
    ).collectiveOffer
    return collective_offer_1, collective_offer_2, collective_offer_3


class ListCollectiveOffersTest(GetEndpointHelper):
    endpoint = "backoffice_web.collective_offer.list_collective_offers"
    needed_permission = perm_models.Permissions.READ_OFFERS

    # Use assert_num_queries() instead of assert_no_duplicated_queries() which does not detect one extra query caused
    # by a field added in the jinja template.
    # - fetch session (1 query)
    # - fetch user (1 query)
    # - fetch collective offers with joinedload including extra data (1 query)
    expected_num_queries = 3

    def test_list_collective_offers_without_filter(self, authenticated_client, collective_offers):
        with assert_num_queries(self.expected_num_queries - 1):
            response = authenticated_client.get(url_for(self.endpoint))
            assert response.status_code == 200

        assert html_parser.count_table_rows(response.data) == 0

    def test_list_collective_offers_by_id(self, authenticated_client, collective_offers):
        searched_id = str(collective_offers[0].id)
        with assert_num_queries(self.expected_num_queries):
            response = authenticated_client.get(url_for(self.endpoint, q=searched_id))
            assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        assert len(rows) == 1
        assert rows[0]["ID"] == searched_id
        assert rows[0]["Nom de l'offre"] == collective_offers[0].name
        assert rows[0]["Catégorie"] == collective_offers[0].category.pro_label
        assert rows[0]["Sous-catégorie"] == collective_offers[0].subcategory.pro_label
        assert rows[0]["Formats"] == ""
        assert rows[0]["État"] == "Validée"
        assert rows[0]["Date de création"] == (datetime.date.today() - datetime.timedelta(days=5)).strftime("%d/%m/%Y")
        assert rows[0]["Date de l'évènement"] == datetime.date.today().strftime("%d/%m/%Y")
        assert rows[0]["Structure"] == collective_offers[0].venue.managingOfferer.name
        assert rows[0]["Lieu"] == collective_offers[0].venue.name

    def test_list_collective_offers_by_name(self, authenticated_client, collective_offers):
        searched_name = collective_offers[1].name
        with assert_num_queries(self.expected_num_queries):
            response = authenticated_client.get(url_for(self.endpoint, q=searched_name))
            assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        rows = sorted(rows, key=lambda row: row["Nom de l'offre"])
        assert len(rows) == 2
        assert rows[0]["ID"] == str(collective_offers[1].id)
        assert rows[0]["Nom de l'offre"] == collective_offers[1].name
        assert rows[0]["Catégorie"] == collective_offers[1].category.pro_label
        assert rows[0]["Sous-catégorie"] == collective_offers[1].subcategory.pro_label
        assert rows[0]["Formats"] == ", ".join([fmt.value for fmt in collective_offers[1].formats])
        assert rows[0]["État"] == "Validée"
        assert rows[0]["Date de création"] == (datetime.date.today() - datetime.timedelta(days=5)).strftime("%d/%m/%Y")
        assert rows[0]["Date de l'évènement"] == datetime.date.today().strftime("%d/%m/%Y")
        assert rows[0]["Structure"] == collective_offers[1].venue.managingOfferer.name
        assert rows[0]["Lieu"] == collective_offers[1].venue.name

    def test_list_offers_by_date(self, authenticated_client, collective_offers):
        with assert_num_queries(self.expected_num_queries):
            response = authenticated_client.get(
                url_for(
                    self.endpoint,
                    from_date=(datetime.date.today() - datetime.timedelta(days=3)).isoformat(),
                    to_date=(datetime.date.today() - datetime.timedelta(days=1)).isoformat(),
                )
            )
            assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        assert set(int(row["ID"]) for row in rows) == {collective_offers[2].id}

    def test_list_collective_offers_by_category(self, authenticated_client, collective_offers):
        with assert_num_queries(self.expected_num_queries):
            response = authenticated_client.get(url_for(self.endpoint, category=[categories.CINEMA.id]))
            assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        assert set(int(row["ID"]) for row in rows) == {collective_offers[1].id, collective_offers[2].id}

    def test_list_collective_offers_by_venue(self, authenticated_client, collective_offers):
        venue_id = collective_offers[1].venueId
        with assert_num_queries(self.expected_num_queries + 1):  # +1 because of reloading selected venue in the form
            response = authenticated_client.get(url_for(self.endpoint, venue=[venue_id]))
            assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        assert set(int(row["ID"]) for row in rows) == {collective_offers[1].id}

    def test_list_collective_offers_by_offerer(self, authenticated_client, collective_offers):
        offerer_id = collective_offers[1].venue.managingOffererId
        with assert_num_queries(self.expected_num_queries + 1):  # +1 because of reloading selected offerer in the form
            response = authenticated_client.get(url_for(self.endpoint, offerer=[offerer_id]))
            assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        assert set(int(row["ID"]) for row in rows) == {collective_offers[1].id}

    def test_list_collective_offers_by_status(self, authenticated_client, collective_offers):
        status = collective_offers[2].validation
        with assert_num_queries(self.expected_num_queries):
            response = authenticated_client.get(url_for(self.endpoint, status=[status.value]))
            assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        assert set(int(row["ID"]) for row in rows) == {collective_offers[2].id}
        assert rows[0]["État"] == "Rejetée"

    def test_list_offers_by_all_filters(self, authenticated_client, collective_offers):
        venue_id = collective_offers[2].venueId
        with assert_num_queries(self.expected_num_queries + 1):  # +1 because of reloading selected venue
            response = authenticated_client.get(
                url_for(
                    self.endpoint,
                    q="specific name",
                    category=[categories.CINEMA.id],
                    venue=[venue_id],
                )
            )
            assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        assert set(int(row["ID"]) for row in rows) == {collective_offers[2].id}

    @pytest.mark.parametrize(
        "order,expected_list",
        [
            ("", ["Offre 4", "Offre 3", "Offre 2", "Offre 1"]),
            ("asc", ["Offre 4", "Offre 3", "Offre 2", "Offre 1"]),
            ("desc", ["Offre 1", "Offre 2", "Offre 3", "Offre 4"]),
        ],
    )
    def test_list_offers_pending_from_validated_offerers_sorted_by_date(
        self, authenticated_client, order, expected_list
    ):
        # test results when clicking on pending collective offers link (home page)
        educational_factories.CollectiveOfferFactory(
            validation=offers_models.OfferValidationStatus.PENDING,
            venue__managingOfferer=offerers_factories.NotValidatedOffererFactory(),
        )

        validated_venue = offerers_factories.VenueFactory()
        for days_ago in (2, 4, 1, 3):
            educational_factories.CollectiveOfferFactory(
                name=f"Offre {days_ago}",
                dateCreated=datetime.datetime.utcnow() - datetime.timedelta(days=days_ago),
                validation=offers_models.OfferValidationStatus.PENDING,
                venue=validated_venue,
            )

        with assert_num_queries(self.expected_num_queries):
            response = authenticated_client.get(
                url_for(
                    self.endpoint,
                    status=[offers_models.OfferValidationStatus.PENDING.value],
                    only_validated_offerers="on",
                    sort="dateCreated",
                    order=order,
                )
            )
            assert response.status_code == 200

        # must be sorted, older first
        rows = html_parser.extract_table_rows(response.data)
        assert [row["Nom de l'offre"] for row in rows] == expected_list

    def test_list_collective_offers_with_flagging_rules(self, authenticated_client):
        rule_1 = offers_factories.OfferValidationRuleFactory(name="Règle magique")
        rule_2 = offers_factories.OfferValidationRuleFactory(name="Règle moldue")
        collective_offer = educational_factories.CollectiveStockFactory(
            collectiveOffer__flaggingValidationRules=[rule_1, rule_2],
        ).collectiveOffer

        with assert_num_queries(self.expected_num_queries):
            response = authenticated_client.get(url_for(self.endpoint, q=str(collective_offer.id)))
            assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        assert rows[0]["Règles de conformité"] == ", ".join([rule_1.name, rule_2.name])


class ValidateCollectiveOfferTest(PostEndpointHelper):
    endpoint = "backoffice_web.collective_offer.validate_collective_offer"
    endpoint_kwargs = {"collective_offer_id": 1}
    needed_permission = perm_models.Permissions.PRO_FRAUD_ACTIONS

    def test_validate_collective_offer(self, legit_user, authenticated_client):
        collective_offer_to_validate = educational_factories.CollectiveOfferFactory(
            validation=OfferValidationStatus.PENDING
        )

        response = self.post_to_endpoint(authenticated_client, collective_offer_id=collective_offer_to_validate.id)
        assert response.status_code == 303

        expected_url = url_for("backoffice_web.collective_offer.list_collective_offers", _external=True)
        assert response.location == expected_url

        collective_offer_list_url = url_for(
            "backoffice_web.collective_offer.list_collective_offers",
            q=collective_offer_to_validate.id,
            _external=True,
        )
        response = authenticated_client.get(collective_offer_list_url)

        assert response.status_code == 200
        row = html_parser.extract_table_rows(response.data)
        assert len(row) == 1
        assert row[0]["État"] == "Validée"

        assert collective_offer_to_validate.isActive is True
        assert collective_offer_to_validate.lastValidationType == OfferValidationType.MANUAL

    # TODO (vroullier) 2023-03-24 : remove when we allow validation of rejected collective offers
    def test_cant_validate_non_pending_offer(self, legit_user, authenticated_client):
        collective_offer_to_validate = educational_factories.CollectiveOfferFactory(
            validation=OfferValidationStatus.REJECTED
        )

        response = self.post_to_endpoint(authenticated_client, collective_offer_id=collective_offer_to_validate.id)
        assert response.status_code == 303

        expected_url = url_for("backoffice_web.collective_offer.list_collective_offers", _external=True)
        assert response.location == expected_url

        collective_offer_list_url = url_for(
            "backoffice_web.collective_offer.list_collective_offers",
            q=collective_offer_to_validate.id,
            _external=True,
        )
        response = authenticated_client.get(collective_offer_list_url)

        assert response.status_code == 200
        assert "Seules les offres collectives en attente peuvent être validées" in response.data.decode("utf-8")
        row = html_parser.extract_table_rows(response.data)
        assert len(row) == 1
        assert row[0]["État"] == "Rejetée"


class ValidateCollectiveOfferFormTest(GetEndpointHelper):
    endpoint = "backoffice_web.collective_offer.get_validate_collective_offer_form"
    endpoint_kwargs = {"collective_offer_id": 1}
    needed_permission = perm_models.Permissions.PRO_FRAUD_ACTIONS

    def test_get_validate_form_test(self, legit_user, authenticated_client):
        collective_offer = educational_factories.CollectiveOfferFactory()

        form_url = url_for(self.endpoint, collective_offer_id=collective_offer.id)

        with assert_num_queries(2):  # session + current user
            response = authenticated_client.get(form_url)
            assert response.status_code == 200


class RejectCollectiveOfferTest(PostEndpointHelper):
    endpoint = "backoffice_web.collective_offer.reject_collective_offer"
    endpoint_kwargs = {"collective_offer_id": 1}
    needed_permission = perm_models.Permissions.PRO_FRAUD_ACTIONS

    def test_reject_collective_offer(self, legit_user, authenticated_client):
        collective_offer_to_reject = educational_factories.CollectiveOfferFactory(
            validation=OfferValidationStatus.PENDING
        )

        response = self.post_to_endpoint(authenticated_client, collective_offer_id=collective_offer_to_reject.id)
        assert response.status_code == 303

        expected_url = url_for("backoffice_web.collective_offer.list_collective_offers", _external=True)
        assert response.location == expected_url

        collective_offer_list_url = url_for(
            "backoffice_web.collective_offer.list_collective_offers", q=collective_offer_to_reject.id, _external=True
        )
        response = authenticated_client.get(collective_offer_list_url)

        assert response.status_code == 200
        row = html_parser.extract_table_rows(response.data)
        assert len(row) == 1
        assert row[0]["État"] == "Rejetée"

        assert collective_offer_to_reject.isActive is False
        assert collective_offer_to_reject.lastValidationType == OfferValidationType.MANUAL

    # TODO (vroullier) 2023-03-24 : remove when we allow validation of validated collective offers
    def test_cant_reject_non_pending_offer(self, legit_user, authenticated_client):
        collective_offer_to_reject = educational_factories.CollectiveOfferFactory(
            validation=OfferValidationStatus.APPROVED
        )

        response = self.post_to_endpoint(authenticated_client, collective_offer_id=collective_offer_to_reject.id)
        assert response.status_code == 303

        expected_url = url_for("backoffice_web.collective_offer.list_collective_offers", _external=True)
        assert response.location == expected_url

        collective_offer_list_url = url_for(
            "backoffice_web.collective_offer.list_collective_offers", q=collective_offer_to_reject.id, _external=True
        )
        response = authenticated_client.get(collective_offer_list_url)

        assert response.status_code == 200
        assert "Seules les offres collectives en attente peuvent être rejetées" in response.data.decode("utf-8")
        row = html_parser.extract_table_rows(response.data)
        assert len(row) == 1
        assert row[0]["État"] == "Validée"


class RejectCollectiveOfferFormTest(GetEndpointHelper):
    endpoint = "backoffice_web.collective_offer.get_reject_collective_offer_form"
    endpoint_kwargs = {"collective_offer_id": 1}
    needed_permission = perm_models.Permissions.PRO_FRAUD_ACTIONS

    def test_get_reject_form_test(self, legit_user, authenticated_client):
        collective_offer = educational_factories.CollectiveOfferFactory()

        form_url = url_for(self.endpoint, collective_offer_id=collective_offer.id)

        with assert_num_queries(2):  # session + current user
            response = authenticated_client.get(form_url)
            assert response.status_code == 200


class BatchCollectiveOffersValidateTest(PostEndpointHelper):
    endpoint = "backoffice_web.collective_offer.batch_validate_collective_offers"
    needed_permission = perm_models.Permissions.PRO_FRAUD_ACTIONS

    def test_batch_validate_collective_offers(self, legit_user, authenticated_client):
        collective_offers = educational_factories.CollectiveOfferFactory.create_batch(
            3, validation=OfferValidationStatus.PENDING
        )
        parameter_ids = ",".join(str(collective_offer.id) for collective_offer in collective_offers)
        response = self.post_to_endpoint(authenticated_client, form={"object_ids": parameter_ids})

        assert response.status_code == 303

        expected_url = url_for("backoffice_web.collective_offer.list_collective_offers", _external=True)
        assert response.location == expected_url

        for collective_offer in collective_offers:
            db.session.refresh(collective_offer)
            assert collective_offer.lastValidationDate.strftime("%d/%m/%Y") == datetime.date.today().strftime(
                "%d/%m/%Y"
            )
            assert collective_offer.isActive is True
            assert collective_offer.lastValidationType is OfferValidationType.MANUAL
            assert collective_offer.validation is OfferValidationStatus.APPROVED

        assert len(mails_testing.outbox) == 3

        received_dict = {email.sent_data["To"]: email.sent_data["template"] for email in mails_testing.outbox}
        expected_dict = {
            collective_offers[0].venue.bookingEmail: asdict(TransactionalEmail.OFFER_APPROVAL_TO_PRO.value),
            collective_offers[1].venue.bookingEmail: asdict(TransactionalEmail.OFFER_APPROVAL_TO_PRO.value),
            collective_offers[2].venue.bookingEmail: asdict(TransactionalEmail.OFFER_APPROVAL_TO_PRO.value),
        }
        assert received_dict == expected_dict

    def test_batch_validate_collective_offers_wrong_id(self, legit_user, authenticated_client):
        fake_offer_ids = [123, 456]
        collective_offer = educational_factories.CollectiveOfferFactory(validation=OfferValidationStatus.PENDING)
        parameter_ids = f"{str(fake_offer_ids[0])}, {str(fake_offer_ids[1])}, {collective_offer}"
        response = self.post_to_endpoint(authenticated_client, form={"object_ids": parameter_ids})

        assert response.status_code == 303
        assert collective_offer.validation == OfferValidationStatus.PENDING
        collective_offer_template = educational_models.CollectiveOffer.query.get(collective_offer.id)
        assert collective_offer_template.validation == OfferValidationStatus.PENDING
        non_existing_collective_offers = educational_models.CollectiveOffer.query.filter(
            educational_models.CollectiveOffer.id.in_(fake_offer_ids)
        ).all()
        assert len(non_existing_collective_offers) == 0


class BatchCollectiveOffersRejectTest(PostEndpointHelper):
    endpoint = "backoffice_web.collective_offer.batch_reject_collective_offers"
    needed_permission = perm_models.Permissions.PRO_FRAUD_ACTIONS

    def test_batch_reject_offers(self, legit_user, authenticated_client):
        collective_offers = educational_factories.CollectiveOfferFactory.create_batch(
            3, validation=OfferValidationStatus.PENDING
        )
        parameter_ids = ",".join(str(collective_offer.id) for collective_offer in collective_offers)

        response = self.post_to_endpoint(authenticated_client, form={"object_ids": parameter_ids})

        assert response.status_code == 303

        expected_url = url_for("backoffice_web.collective_offer.list_collective_offers", _external=True)
        assert response.location == expected_url

        for collective_offer in collective_offers:
            db.session.refresh(collective_offer)
            assert collective_offer.lastValidationDate.strftime("%d/%m/%Y") == datetime.date.today().strftime(
                "%d/%m/%Y"
            )
            assert collective_offer.isActive is False
            assert collective_offer.lastValidationType is OfferValidationType.MANUAL
            assert collective_offer.validation is OfferValidationStatus.REJECTED
            assert collective_offer.lastValidationAuthor == legit_user

        assert len(mails_testing.outbox) == 3

        received_dict = {email.sent_data["To"]: email.sent_data["template"] for email in mails_testing.outbox}
        expected_dict = {
            collective_offers[0].venue.bookingEmail: asdict(TransactionalEmail.OFFER_PENDING_TO_REJECTED_TO_PRO.value),
            collective_offers[1].venue.bookingEmail: asdict(TransactionalEmail.OFFER_PENDING_TO_REJECTED_TO_PRO.value),
            collective_offers[2].venue.bookingEmail: asdict(TransactionalEmail.OFFER_PENDING_TO_REJECTED_TO_PRO.value),
        }
        assert received_dict == expected_dict

    def test_batch_reject_collective_offers_wrong_id(self, legit_user, authenticated_client):
        fake_offer_ids = [123, 456]
        collective_offer = educational_factories.CollectiveOfferFactory(validation=OfferValidationStatus.PENDING)
        parameter_ids = f"{str(fake_offer_ids[0])}, {str(fake_offer_ids[1])}, {collective_offer}"
        response = self.post_to_endpoint(authenticated_client, form={"object_ids": parameter_ids})

        assert response.status_code == 303
        assert collective_offer.validation == OfferValidationStatus.PENDING
        collective_offer_template = educational_models.CollectiveOffer.query.get(collective_offer.id)
        assert collective_offer_template.validation == OfferValidationStatus.PENDING
        non_existing_collective_offers = educational_models.CollectiveOffer.query.filter(
            educational_models.CollectiveOffer.id.in_(fake_offer_ids)
        ).all()
        assert len(non_existing_collective_offers) == 0


class GetBatchCollectiveOffersApproveFormTest(GetEndpointHelper):
    endpoint = "backoffice_web.collective_offer.get_batch_validate_collective_offers_form"
    needed_permission = perm_models.Permissions.PRO_FRAUD_ACTIONS

    def test_get_batch_collective_offers_approve_form(self, legit_user, authenticated_client):
        url = url_for(self.endpoint)

        with assert_num_queries(2):  # session + current user
            response = authenticated_client.get(url)
            assert response.status_code == 200


class GetBatchCollectiveOffersRejectFormTest(GetEndpointHelper):
    endpoint = "backoffice_web.collective_offer.get_batch_reject_collective_offers_form"
    needed_permission = perm_models.Permissions.PRO_FRAUD_ACTIONS

    def test_get_batch_collective_offers_reject_form(self, legit_user, authenticated_client):
        url = url_for(self.endpoint)

        with assert_num_queries(2):  # session + current user
            response = authenticated_client.get(url)
            assert response.status_code == 200


class GetCollectiveOfferDetailTest(GetEndpointHelper):
    endpoint = "backoffice_web.collective_offer.get_collective_offer_details"
    endpoint_kwargs = {"collective_offer_id": 1}
    needed_permission = perm_models.Permissions.READ_OFFERS

    def test_nominal(self, legit_user, authenticated_client):
        event_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        collective_booking = educational_factories.CollectiveBookingFactory(
            collectiveStock__beginningDatetime=event_date,
        )
        url = url_for(self.endpoint, collective_offer_id=collective_booking.collectiveStock.collectiveOffer.id)
        with assert_num_queries(4):
            response = authenticated_client.get(url)
            assert response.status_code == 200

        content_as_text = html_parser.content_as_text(response.data)
        assert "Ajuster le prix de l'offre" in content_as_text
        assert "Statut : Expirée" in content_as_text
        assert "État : Validée" in content_as_text
        assert "Utilisateur de la dernière validation" not in content_as_text
        assert "Date de dernière validation de l’offre" not in content_as_text

    def test_processed_pricing(self, legit_user, authenticated_client):
        pricing = finance_factories.CollectivePricingFactory(
            status=finance_models.PricingStatus.PROCESSED,
            collectiveBooking__collectiveStock__beginningDatetime=datetime.datetime(1970, 1, 1),
        )
        url = url_for(self.endpoint, collective_offer_id=pricing.collectiveBooking.collectiveStock.collectiveOffer.id)

        with assert_num_queries(4):
            response = authenticated_client.get(url)
            assert response.status_code == 200

        assert "Ajuster le prix de l'offre" not in response.data.decode()

    def test_invoiced_pricing(self, legit_user, authenticated_client):
        pricing = finance_factories.CollectivePricingFactory(
            status=finance_models.PricingStatus.INVOICED,
            collectiveBooking__collectiveStock__beginningDatetime=datetime.datetime(1970, 1, 1),
        )
        url = url_for(self.endpoint, collective_offer_id=pricing.collectiveBooking.collectiveStock.collectiveOffer.id)

        with assert_num_queries(4):
            response = authenticated_client.get(url)
            assert response.status_code == 200

        assert "Ajuster le prix de l'offre" not in response.data.decode()

    def test_cashflow_pending(self, legit_user, authenticated_client, app):
        pricing = finance_factories.CollectivePricingFactory(
            collectiveBooking__collectiveStock__beginningDatetime=datetime.datetime(1970, 1, 1),
        )
        url = url_for(self.endpoint, collective_offer_id=pricing.collectiveBooking.collectiveStock.collectiveOffer.id)
        app.redis_client.set(finance_conf.REDIS_GENERATE_CASHFLOW_LOCK, "1", 600)
        try:
            with assert_num_queries(3):
                response = authenticated_client.get(url)
                assert response.status_code == 200
        finally:
            app.redis_client.delete(finance_conf.REDIS_GENERATE_CASHFLOW_LOCK)

        assert "Ajuster le prix de l'offre" not in response.data.decode()

    def test_get_validated_offer(self, legit_user, authenticated_client):
        event_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        validation_date = datetime.datetime.utcnow()
        collective_booking = educational_factories.CollectiveBookingFactory(
            collectiveStock__beginningDatetime=event_date,
            collectiveStock__collectiveOffer__lastValidationDate=validation_date,
            collectiveStock__collectiveOffer__validation=offers_models.OfferValidationStatus.APPROVED,
            collectiveStock__collectiveOffer__lastValidationAuthor=legit_user,
        )
        url = url_for(self.endpoint, collective_offer_id=collective_booking.collectiveStock.collectiveOffer.id)
        with assert_num_queries(4):  # session + user + offer + pricing + loaded data
            response = authenticated_client.get(url)

        content_as_text = html_parser.content_as_text(response.data)
        assert response.status_code == 200
        assert f"Utilisateur de la dernière validation : {legit_user.full_name}" in content_as_text
        assert f"Date de dernière validation : {format_date(validation_date, '%d/%m/%Y à %Hh%M')}" in content_as_text

    def test_get_rejected_offer(self, legit_user, authenticated_client):
        event_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        validation_date = datetime.datetime.utcnow()
        collective_booking = educational_factories.CollectiveBookingFactory(
            collectiveStock__beginningDatetime=event_date,
            collectiveStock__collectiveOffer__lastValidationDate=validation_date,
            collectiveStock__collectiveOffer__validation=offers_models.OfferValidationStatus.REJECTED,
            collectiveStock__collectiveOffer__lastValidationAuthor=legit_user,
        )
        url = url_for(self.endpoint, collective_offer_id=collective_booking.collectiveStock.collectiveOffer.id)
        with assert_num_queries(4):  # session + user + offer + pricing + loaded data
            response = authenticated_client.get(url)
            assert response.status_code == 200

        content_as_text = html_parser.content_as_text(response.data)
        assert f"Utilisateur de la dernière validation : {legit_user.full_name}" in content_as_text
        assert f"Date de dernière validation : {format_date(validation_date, '%d/%m/%Y à %Hh%M')}" in content_as_text


class GetCollectiveOfferPriceFormTest(GetEndpointHelper):
    endpoint = "backoffice_web.collective_offer.get_collective_offer_price_form"
    endpoint_kwargs = {"collective_offer_id": 1}
    needed_permission = perm_models.Permissions.ADVANCED_PRO_SUPPORT

    # session + current user + offer + stock
    expected_num_queries = 4

    def test_get_collective_offer_price_form(self, legit_user, authenticated_client):
        collective_offer_id = educational_factories.CollectiveStockFactory().collectiveOfferId

        with assert_num_queries(self.expected_num_queries):
            response = authenticated_client.get(url_for(self.endpoint, collective_offer_id=collective_offer_id))
            assert response.status_code == 200


class PostEditCollectiveOfferPriceTest(PostEndpointHelper):
    endpoint = "backoffice_web.collective_offer.edit_collective_offer_price"
    endpoint_kwargs = {"collective_offer_id": 1}
    needed_permission = perm_models.Permissions.ADVANCED_PRO_SUPPORT

    def test_nominal(self, legit_user, authenticated_client):
        venue = offerers_factories.VenueFactory(pricing_point="self")
        date_used = datetime.datetime.utcnow() - datetime.timedelta(hours=72)
        collective_booking = educational_factories.UsedCollectiveBookingFactory(
            collectiveStock__price=Decimal(100.00),
            collectiveStock__numberOfTickets=25,
            collectiveStock__beginningDatetime=date_used,
            venue=venue,
            dateUsed=date_used,
        )
        finance_api.add_event(
            finance_models.FinanceEventMotive.BOOKING_USED,
            booking=collective_booking,
        )

        response = self.post_to_endpoint(
            authenticated_client,
            form={"numberOfTickets": 5, "price": 1},
            collective_offer_id=collective_booking.collectiveStock.collectiveOffer.id,
        )

        assert response.status_code == 303
        assert collective_booking.collectiveStock.price == 1
        assert collective_booking.collectiveStock.numberOfTickets == 5
        assert (
            html_parser.extract_alert(authenticated_client.get(response.location).data)
            == "L'offre collective a été mise à jour"
        )

    def test_processed_pricing(self, legit_user, authenticated_client):
        pricing = finance_factories.CollectivePricingFactory(
            status=finance_models.PricingStatus.PROCESSED,
            collectiveBooking__collectiveStock__price=Decimal(100.00),
            collectiveBooking__collectiveStock__numberOfTickets=25,
            collectiveBooking__collectiveStock__beginningDatetime=datetime.datetime(1970, 1, 1),
        )
        url = url_for(self.endpoint, collective_offer_id=pricing.collectiveBooking.collectiveStock.collectiveOffer.id)
        authenticated_client.get(url)

        response = self.post_to_endpoint(
            authenticated_client,
            form={"numberOfTickets": 5, "price": 1},
            collective_offer_id=pricing.collectiveBooking.collectiveStock.collectiveOffer.id,
        )

        assert response.status_code == 303
        assert pricing.collectiveBooking.collectiveStock.price == 100
        assert pricing.collectiveBooking.collectiveStock.numberOfTickets == 25
        assert (
            html_parser.extract_alert(authenticated_client.get(response.location).data)
            == "Cette offre n'est pas modifiable"
        )

    def test_invoiced_pricing(self, legit_user, authenticated_client):
        pricing = finance_factories.CollectivePricingFactory(
            status=finance_models.PricingStatus.INVOICED,
            collectiveBooking__collectiveStock__price=Decimal(100.00),
            collectiveBooking__collectiveStock__numberOfTickets=25,
            collectiveBooking__collectiveStock__beginningDatetime=datetime.datetime(1970, 1, 1),
        )
        url = url_for(self.endpoint, collective_offer_id=pricing.collectiveBooking.collectiveStock.collectiveOffer.id)
        authenticated_client.get(url)

        response = self.post_to_endpoint(
            authenticated_client,
            form={"numberOfTickets": 5, "price": 1},
            collective_offer_id=pricing.collectiveBooking.collectiveStock.collectiveOffer.id,
        )

        assert response.status_code == 303
        assert pricing.collectiveBooking.collectiveStock.price == 100
        assert pricing.collectiveBooking.collectiveStock.numberOfTickets == 25
        assert (
            html_parser.extract_alert(authenticated_client.get(response.location).data)
            == "Cette offre n'est pas modifiable"
        )

    @pytest.mark.parametrize(
        "pricing_status",
        [
            finance_models.PricingStatus.CANCELLED,
            finance_models.PricingStatus.VALIDATED,
            finance_models.PricingStatus.PENDING,
            finance_models.PricingStatus.REJECTED,
        ],
    )
    def test_unprocessed_pricing(self, legit_user, authenticated_client, pricing_status):
        # when
        pricing = finance_factories.CollectivePricingFactory(
            status=pricing_status,
            collectiveBooking__collectiveStock__price=Decimal(100.00),
            collectiveBooking__collectiveStock__numberOfTickets=25,
            collectiveBooking__collectiveStock__beginningDatetime=datetime.datetime(1970, 1, 1),
        )

        response = self.post_to_endpoint(
            authenticated_client,
            form={"numberOfTickets": 5, "price": 1},
            collective_offer_id=pricing.collectiveBooking.collectiveStock.collectiveOffer.id,
        )

        # then
        assert response.status_code == 303
        assert pricing.collectiveBooking.collectiveStock.price == 1
        assert pricing.collectiveBooking.collectiveStock.numberOfTickets == 5
        assert (
            html_parser.extract_alert(authenticated_client.get(response.location).data)
            == "L'offre collective a été mise à jour"
        )

    def test_cashflow_pending(self, legit_user, authenticated_client, app):
        event_date = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        collective_booking = educational_factories.CollectiveBookingFactory(
            collectiveStock__price=Decimal(100.00),
            collectiveStock__numberOfTickets=25,
            collectiveStock__beginningDatetime=event_date,
        )
        app.redis_client.set(finance_conf.REDIS_GENERATE_CASHFLOW_LOCK, "1", 600)
        try:
            response = self.post_to_endpoint(
                authenticated_client,
                form={"numberOfTickets": 5, "price": 1},
                collective_offer_id=collective_booking.collectiveStock.collectiveOffer.id,
            )
        finally:
            app.redis_client.delete(finance_conf.REDIS_GENERATE_CASHFLOW_LOCK)

        assert response.status_code == 303
        assert collective_booking.collectiveStock.price == 100
        assert collective_booking.collectiveStock.numberOfTickets == 25
        assert (
            html_parser.extract_alert(authenticated_client.get(response.location).data)
            == "Cette offre n'est pas modifiable"
        )

    @pytest.mark.parametrize(
        "booking_status",
        [
            educational_models.CollectiveBookingStatus.CANCELLED,
            educational_models.CollectiveBookingStatus.PENDING,
            educational_models.CollectiveBookingStatus.CONFIRMED,
            educational_models.CollectiveBookingStatus.USED,
        ],
    )
    def test_price_higher_than_previously(self, legit_user, authenticated_client, booking_status):
        now = datetime.datetime.utcnow()
        collective_booking = educational_factories.CollectiveBookingFactory(
            collectiveStock__price=Decimal(100.00),
            collectiveStock__numberOfTickets=25,
            collectiveStock__beginningDatetime=now,
            status=booking_status,
            dateUsed=now,
            confirmationDate=now,
        )
        response = self.post_to_endpoint(
            authenticated_client,
            form={"numberOfTickets": 5, "price": 200},
            collective_offer_id=collective_booking.collectiveStock.collectiveOffer.id,
        )

        if booking_status in [
            educational_models.CollectiveBookingStatus.CONFIRMED,
            educational_models.CollectiveBookingStatus.USED,
        ]:
            assert response.status_code == 303
            assert collective_booking.collectiveStock.price == 100
            assert collective_booking.collectiveStock.numberOfTickets == 25
            assert (
                html_parser.extract_alert(authenticated_client.get(response.location).data)
                == "Impossible d'augmenter le prix d'une offre confirmée"
            )
        else:
            assert response.status_code == 303
            assert collective_booking.collectiveStock.price == 200
            assert collective_booking.collectiveStock.numberOfTickets == 5

    @pytest.mark.parametrize(
        "booking_status",
        [
            educational_models.CollectiveBookingStatus.CANCELLED,
            educational_models.CollectiveBookingStatus.PENDING,
            educational_models.CollectiveBookingStatus.CONFIRMED,
            educational_models.CollectiveBookingStatus.USED,
        ],
    )
    def test_number_of_tickets_higher_than_previously(self, legit_user, authenticated_client, booking_status):
        now = datetime.datetime.utcnow()
        collective_booking = educational_factories.CollectiveBookingFactory(
            collectiveStock__price=Decimal(100.00),
            collectiveStock__numberOfTickets=25,
            collectiveStock__beginningDatetime=now,
            status=booking_status,
            dateUsed=now,
            confirmationDate=now,
        )
        response = self.post_to_endpoint(
            authenticated_client,
            form={"numberOfTickets": 50, "price": 1},
            collective_offer_id=collective_booking.collectiveStock.collectiveOffer.id,
        )

        if booking_status in [
            educational_models.CollectiveBookingStatus.CONFIRMED,
            educational_models.CollectiveBookingStatus.USED,
        ]:
            assert response.status_code == 303
            assert collective_booking.collectiveStock.price == 100
            assert collective_booking.collectiveStock.numberOfTickets == 25
            assert (
                html_parser.extract_alert(authenticated_client.get(response.location).data)
                == "Impossible d'augmenter le nombre de participants d'une offre confirmée"
            )
        else:
            assert response.status_code == 303
            assert collective_booking.collectiveStock.price == 1
            assert collective_booking.collectiveStock.numberOfTickets == 50
