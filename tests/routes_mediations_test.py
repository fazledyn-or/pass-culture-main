from os import path
from pathlib import Path

import pytest

from models import PcObject, Mediation
from tests.conftest import clean_database
from utils.human_ids import humanize
from utils.test_utils import API_URL, req_with_auth, create_user, create_offerer, create_user_offerer, \
    create_event_offer, create_venue, create_mediation


@clean_database
@pytest.mark.standalone
def test_create_mediation_with_thumb(app):
    # given
    user = create_user(password='p@55sw0rd')
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_event_offer(venue)
    user_offerer = create_user_offerer(user, offerer)

    PcObject.check_and_save(offer)
    PcObject.check_and_save(user, venue, offerer, user_offerer)

    auth_request = req_with_auth(email=user.email, password='p@55sw0rd')

    with open(Path(path.dirname(path.realpath(__file__))) / '..'
              / 'mock' / 'thumbs' / 'mediations' / '1', 'rb') as thumb_file:
        data = {'offerId': humanize(offer.id), 'offererId': humanize(offerer.id), }
        files = {'thumb': ('1.jpg', thumb_file)}

        # when
        response = auth_request.post(API_URL + '/mediations', data=data, files=files)

    # then
    assert response.status_code == 201


@clean_database
@pytest.mark.standalone
def test_delete_mediation_returns_200_and_effectively_remove_the_mediation(app):
    # given
    user = create_user(password='p@55sw0rd')
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_event_offer(venue)
    user_offerer = create_user_offerer(user, offerer)
    mediation = create_mediation(offer)
    PcObject.check_and_save(mediation)
    PcObject.check_and_save(offer)
    PcObject.check_and_save(user, venue, offerer, user_offerer)

    auth_request = req_with_auth(email=user.email, password='p@55sw0rd')

    # when
    response = auth_request.delete(API_URL + '/mediations/%s' % humanize(mediation.id))

    # then
    assert response.status_code == 200
    assert response.json()['id'] == humanize(mediation.id)
    assert Mediation.query.filter_by(id=mediation.id).all() == []


@clean_database
@pytest.mark.standalone
def test_delete_mediation_returns_400_if_user_is_not_attached_to_offerer_of_mediation(app):
    # given
    current_user = create_user(email='bobby@test.com', password='p@55sw0rd')
    other_user = create_user(email='jimmy@test.com', password='p@55sw0rd')
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_event_offer(venue)
    user_offerer = create_user_offerer(other_user, offerer)
    mediation = create_mediation(offer)
    PcObject.check_and_save(mediation)
    PcObject.check_and_save(other_user, current_user, venue, offerer, user_offerer)

    auth_request = req_with_auth(email=current_user.email, password='p@55sw0rd')

    # when
    response = auth_request.delete(API_URL + '/mediations/%s' % humanize(mediation.id))

    # then
    assert response.status_code == 400


@clean_database
@pytest.mark.standalone
def test_delete_mediation_returns_404_if_mediation_does_not_exist(app):
    # given
    user = create_user(password='p@55sw0rd')
    PcObject.check_and_save(user)
    auth_request = req_with_auth(email=user.email, password='p@55sw0rd')

    # when
    response = auth_request.delete(API_URL + '/mediations/AE')

    # then
    assert response.status_code == 404


@clean_database
@pytest.mark.standalone
def test_get_mediation_returns_200_and_the_mediation_as_json(app):
    # given
    user = create_user(password='p@55sw0rd')
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_event_offer(venue)
    user_offerer = create_user_offerer(user, offerer)
    mediation = create_mediation(offer)
    PcObject.check_and_save(mediation)
    PcObject.check_and_save(offer)
    PcObject.check_and_save(user, venue, offerer, user_offerer)

    auth_request = req_with_auth(email=user.email, password='p@55sw0rd')

    # when
    response = auth_request.get(API_URL + '/mediations/%s' % humanize(mediation.id))

    # then
    assert response.status_code == 200
    assert response.json()['id'] == humanize(mediation.id)
    assert response.json()['frontText'] == mediation.frontText
    assert response.json()['backText'] == mediation.backText


@clean_database
@pytest.mark.standalone
def test_get_mediation_returns_404_if_mediation_does_not_exist(app):
    # given
    user = create_user(password='p@55sw0rd')
    PcObject.check_and_save(user)
    auth_request = req_with_auth(email=user.email, password='p@55sw0rd')

    # when
    response = auth_request.get(API_URL + '/mediations/AE')

    # then
    assert response.status_code == 404
