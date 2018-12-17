import pytest
from tests.conftest import clean_database

from sandboxes.scripts.save_sandbox import save_sandbox
from utils.logger import logger
from utils.test_utils import assertCreatedCounts, \
                             saveCounts

@clean_database
@pytest.mark.standalone
def test_save_industrial_sandbox(app):
    savedCounts = {}
    saveCounts(app)
    with app.app_context():
        logger_info = logger.info
        logger.info = lambda o: None
        save_sandbox('industrial')
        logger.info = logger_info
        assertCreatedCounts(
            app,
            Booking=24,
            Deposit=6,
            Event=8,
            EventOccurrence=144,
            Mediation=114,
            Offer=114,
            Offerer=6,
            Recommendation=24,
            Stock=192,
            Thing=11,
            User=20,
            UserOfferer=60,
            Venue=12
        )
