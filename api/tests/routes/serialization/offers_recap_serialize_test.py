from pcapi.core.categories import subcategories
from pcapi.domain.pro_offers.offers_recap import OfferRecap
from pcapi.domain.pro_offers.offers_recap import OffersRecap
from pcapi.routes.serialization.offers_recap_serialize import serialize_offers_recap_paginated


def should_return_serialized_offers_with_relevant_informations():
    # given
    offer_id = 1
    stock_id = 2
    venue_id = 3
    offerer_id = 4
    stock = {
        "id": stock_id,
        "has_booking_limit_datetime_passed": False,
        "remaining_quantity": 10,
        "beginning_datetime": None,
        "dnBookedQuantity": 0,
    }
    departement_code = 12
    offer = OfferRecap(
        id=offer_id,
        has_booking_limit_datetimes_passed=False,
        is_active=True,
        is_editable=True,
        is_event=False,
        is_thing=True,
        product_ean=None,
        name="Test Book",
        thumb_url="/thumb/url",
        subcategory_id=subcategories.SUPPORT_PHYSIQUE_FILM.id,
        venue_id=venue_id,
        venue_is_virtual=False,
        venue_managing_offerer_id=offerer_id,
        venue_name="La petite librairie",
        venue_public_name="Petite librairie",
        venue_offerer_name="Gérant de petites librairies",
        venue_departement_code=departement_code,
        stocks=[stock],
        status="ACTIVE",
        is_showcase=False,
    )
    offers_recap = OffersRecap(offers_recap=[offer])

    # when
    result = serialize_offers_recap_paginated(offers_recap)

    # then
    expected_serialized_offer = [
        {
            "hasBookingLimitDatetimesPassed": False,
            "id": offer_id,
            "isActive": True,
            "isEditable": True,
            "isEvent": False,
            "isThing": True,
            "isEducational": False,
            "productIsbn": None,
            "name": "Test Book",
            "status": "ACTIVE",
            "stocks": [
                {
                    "hasBookingLimitDatetimePassed": False,
                    "id": stock_id,
                    "remainingQuantity": 10,
                    "beginningDatetime": None,
                    "bookingQuantity": 0,
                }
            ],
            "subcategoryId": "SUPPORT_PHYSIQUE_FILM",
            "thumbUrl": "/thumb/url",
            "venue": {
                "id": venue_id,
                "isVirtual": False,
                "departementCode": departement_code,
                "name": "La petite librairie",
                "offererName": "Gérant de petites librairies",
                "publicName": "Petite librairie",
            },
            "isShowcase": False,
        }
    ]
    assert result == expected_serialized_offer
