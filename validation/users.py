from models import ApiErrors


def check_allowed_changes_for_user(data):
    changes_allowed = {'email', 'publicName', 'postalCode', 'phoneNumber', 'departementCode'}
    changes_asked = set(data)
    api_errors = ApiErrors()
    changes_not_allowed = changes_asked.difference(changes_allowed)
    if changes_not_allowed:
        for change in changes_not_allowed:
            api_errors.addError(change, 'Vous ne pouvez pas changer cette information')
        raise api_errors


def check_contact_ok(contact_ok):
    if not contact_ok or _contact_ok_is_not_checked(contact_ok):
        e = ApiErrors()
        e.addError('contact_ok', 'Vous devez obligatoirement cocher cette case')
        raise e


def _contact_ok_is_not_checked(contact_ok):
    contact_ok_is_not_checked_as_bool = contact_ok is not True
    contact_ok_is_not_checked_as_str = str(contact_ok).lower() != 'true'
    return contact_ok_is_not_checked_as_bool and contact_ok_is_not_checked_as_str
