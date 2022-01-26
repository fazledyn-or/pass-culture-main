import pytest

from pcapi.core.bookings import models as bookings_models
from pcapi.core.educational import models as educational_models
from pcapi.core.finance import models as finance_models
from pcapi.core.offerers import models as offerers_models
from pcapi.core.offers import models as offers_models
from pcapi.core.reference import models as reference_models
from pcapi.repository.clean_database import clean_all_database
from pcapi.sandboxes.scripts.creators.industrial import save_industrial_sandbox


@pytest.mark.skip("This is a very long-running test used to help working on the sandbox")
class SaveIndustrialSandboxTest:
    def test_creations(self, clear_tests_invoices_bucket):
        clean_all_database()

        save_industrial_sandbox()

        assert offerers_models.Offerer.query.count() == 19
        assert offerers_models.Venue.query.count() == 28
        assert finance_models.BusinessUnit.query.count() == 28
        assert offers_models.Offer.query.count() == 182
        assert offers_models.Stock.query.count() == 182
        assert 302 <= bookings_models.Booking.query.count() <= 306
        assert 182 <= bookings_models.IndividualBooking.query.count() <= 186
        assert 118 <= educational_models.EducationalBooking.query.count() <= 122
        assert reference_models.ReferenceScheme.query.count() == 2
        assert finance_models.Invoice.query.count() == 5
        assert finance_models.Cashflow.query.count() == 5
        assert (
            finance_models.Pricing.query.filter(
                finance_models.Pricing.status != finance_models.PricingStatus.INVOICED
            ).count()
        ) == 0
