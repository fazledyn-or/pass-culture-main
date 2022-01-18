import datetime

import pytest

import pcapi.core.bookings.api as bookings_api
import pcapi.core.bookings.factories as bookings_factories
from pcapi.core.finance import api
from pcapi.core.finance import models
import pcapi.core.reference.factories as reference_factories
from pcapi.models import db


pytestmark = pytest.mark.usefixtures("db_session")


def test_integration():
    booking = bookings_factories.IndividualBookingFactory()
    bookings_api.mark_as_used(booking)
    pricing = api.price_booking(booking)
    assert pricing.status == models.PricingStatus.VALIDATED

    cutoff = datetime.datetime.utcnow()
    api.generate_cashflows_and_payment_files(cutoff)
    assert len(pricing.cashflows) == 1
    cashflow = pricing.cashflows[0]
    assert cashflow.status == models.CashflowStatus.UNDER_REVIEW
    db.session.refresh(pricing)
    assert pricing.status == models.PricingStatus.PROCESSED

    reference_factories.ReferenceSchemeFactory()
    api._generate_invoice(pricing.businessUnitId, [cashflow.id])
    db.session.refresh(pricing)
    assert pricing.status == models.PricingStatus.INVOICED
