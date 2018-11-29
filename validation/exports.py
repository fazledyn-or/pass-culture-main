from models.api_errors import ForbiddenError

from models import ApiErrors
import re

def check_user_is_admin(user):
    if not user.isAdmin:
        api_errors = ForbiddenError()
        api_errors.addError('isAdmin', 'Vous devez être admin')
        raise api_errors


def check_get_venues_params(param: {}) -> []:
    if param.get('dpt', []):
        _check_dpt_list(param['dpt'])

    if param.get('has_validated_offerer', None):
        _check_has_validated_offerer_param(param['has_validated_offerer'])

    if param.get('zip_codes', []):
        _check_zip_codes_list(param['zip_codes'])

    if param.get('from_date', None):
        _check_date_format(param['from_date'])

    if param.get('to_date', None):
        _check_date_format(param['to_date'])

    if param.get('has_siret', None):
        _check_has_siret_param(param['has_siret'])

    if param.get('is_virtual', None):
        _check_is_virtual_param(param['is_virtual'])

    if param.get('has_offer', None):
        _check_has_offer_param(param['has_offer'])

    if param.get('is_validated', None):
        _check_is_validated_param(param['is_validated'])

    return True


def _check_date_format(date: str) -> bool:
    if re.search('^\d{4}-\d{2}-\d{2}$', date):
       return True
    api_errors = ApiErrors()
    api_errors.addError('date_format', 'to_date and from_date are of type yyyy-mm-dd')
    raise api_errors


def _check_dpt_list(dpt_list:  []) -> bool:
    for dpt in dpt_list:
       if not re.search('^\d{2}$|^2{1}(a|b|A|B)$|^\d{3}$', dpt):
            api_errors = ApiErrors()
            api_errors.addError('dpt', 
                'dpt is of type xx or xxx (2 or 3 digits), or 2A, or 2B')
            raise api_errors
    return True


def _check_zip_codes_list(zip_codes_list:  []) -> bool:

    for zip_code in zip_codes_list:
        if not re.search('^\d{5}$|^2{1}(a|b|A|B)\d{3}$', zip_code):
            api_errors = ApiErrors()
            api_errors.addError('zip_codes',
                'zip_codes is of type xxxxx (5 digits, ex: 78140 ou 2a000)')
            raise api_errors
    return True


def _check_has_validated_offerer_param(has_validated_offerer) -> bool:
    if type(has_validated_offerer) == bool:
       return True
    api_errors = ApiErrors()
    api_errors.addError('has_validated_offerer', 'has_validated_offerer is a boolean, it accepts True or False')   
    raise api_errors


def _check_is_virtual_param(is_virtual) -> bool:
    if type(is_virtual) == bool:
       return True
    api_errors = ApiErrors()
    api_errors.addError('is_virtual', 'is_virtual is a boolean, it accepts True or False')   
    raise api_errors


def _check_has_offer_param(has_offer: str) -> bool:
    valid_param = ['ALL', 'VALID', 'WITHOUT', 'EXPIRED']
    for elem in valid_param:
        if has_offer == elem:
            return True
    api_errors = ApiErrors()
    api_errors.addError('has_offer', 'has_offer accepte ALL ou VALID ou WITHOUT ou EXPIRED')
    raise api_errors


def _check_has_siret_param(has_siret) -> bool:
    if type(has_siret) == bool:
       return True
    api_errors = ApiErrors()
    api_errors.addError('has_siret', 'has_siret is a boolean, it accepts True or False')   
    raise api_errors


def _check_is_validated_param(is_validated) -> bool:
    if type(is_validated) == bool:
       return True
    api_errors = ApiErrors()
    api_errors.addError('is_validated', 'is_validated is a boolean, it accepts True or False')   
    raise api_errors
