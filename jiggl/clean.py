from datetime import timedelta
import re

import curried_toolz as z
from jiggl.utils import error, success, bind, unit
from sources.ggl import toggl_strptime, JIGGLD_TAG
from sources.ji import jira_strftime
from utils import has_error


def is_not_already_logged(entry):
    if JIGGLD_TAG in entry.get('tags', []):
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
    if any(re.match(r'%s-[\d]+.*' % pkey, description) for pkey in ['SARR', 'TIMPA', 'MS', 'CGFM', 'MDC']):
        return success(entry)
    return error(entry, 'Invalid description')


m_is_valid_description = bind(is_valid_description)


def has_significant_duration(entry):
    """
    If a duration is too small, then jira doesn't like it. Plus, there's no reason to log it...
    :param entry:
    :return:
    """
    duration = entry['duration']
    if duration < 60 * 5:
        return error(entry, 'Duration is too small: %s seconds' % duration)
    return success(entry)

m_has_significant_duration = bind(has_significant_duration)

_validate_one = z.compose(
    m_has_significant_duration,
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


def split_description(group):
    description, entries = group
    parts = description.split(' ', 1)
    # Allow for descriptions with a Jira task identifier but no accomanying description
    if len(parts) > 1:
        return parts, entries
    return (parts[0], ''), entries


def _split_description(description):
    parts = description.split(' ', 1)
    if len(parts) > 1:
        return tuple(parts)
    return description, ''


sum_as_timedelta = lambda entries: timedelta(seconds=total_duration(entries))
total_duration = z.compose(sum, z.pluck('duration', default=0))
toggl_to_jira_datefmt = z.compose(
    jira_strftime,
    toggl_strptime,
)
get_valid_invalid = z.get([False, True], default=[])
group_by_has_error = z.groupby(has_error)
split_entries = z.compose(
    get_valid_invalid,
    group_by_has_error,
    validate_many,
)