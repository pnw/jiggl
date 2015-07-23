import re
import toolz as z
from jiggl.utils import error, success, bind, unit


def is_not_already_logged(entry):
    if 'jiggl' in entry.get('tags', []):
        return error(entry, 'Already logged')
    return success(entry)


m_is_not_already_logged = bind(is_not_already_logged)


def is_not_currently_logging(entry):
    if entry['duration'] < 0:
        return error(entry, 'Currently logging')
    return success(entry)


m_is_not_currently_logging = bind(is_not_currently_logging)


def is_valid_description(entry):
    """
    If the entry starts with a valid jira ticket
    :param entry:
    :return:
    """
    try:
        description = entry['description']
    except KeyError:
        return error(entry, 'Missing description')
    if any(re.match(r'%s-[\d]+.*' % pkey, description) for pkey in ['SARR', 'TMP']):
        return success(entry)
    return error(entry, 'Invalid description')


m_is_valid_description = bind(is_valid_description)

_validate_one = z.compose(
    m_is_not_already_logged,
    m_is_not_currently_logging,
    m_is_valid_description,
    unit
)


def validate_one(entry):
    """
    Passes the entry through a number of validation criteria,
    returning the entry and, if invalid, an error describing why the entry is not valid, or None if not.

    :param entry: An entry from the Toggl API
    :type entry: dict
    :return: (entry, error)
    :rtype: (dict, str)
    """
    return _validate_one(entry)


validate_many = z.curry(z.map, validate_one)
