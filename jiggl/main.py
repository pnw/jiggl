from collections import defaultdict
from datetime import timedelta
import functools
import json
import os
import re

from PyToggl.PyToggl import PyToggl
import requests

# from ggl import JIGGLD
# from ji import jira_project_keys
from jiggl.clean import validate_one
from jiggl.utils import has_no_error, get_val
from jiggl.utils import has_error

try:
    from jiggl import settings
    from jiggl.colors import bcolors
except ImportError:
    # for when we invoke the script directly
    import settings
    from colors import bcolors


def get_entries():
    current_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_path, 'fixtures', 'entries.json')) as f:
        return json.load(f)


def _query(self, url, params, method, query_type=None, return_type='json'):
    if query_type == 'report':
        api_url = self.api_reports_url + url
    else:
        api_url = self.api_url + url

    auth = (self.api_token, 'api_token')
    headers = {'content-type': 'application/json'}

    if method == "POST":
        response = requests.post(api_url, auth=auth, headers=headers, params=params)
    elif method == "GET":
        response = requests.get(api_url, auth=auth, headers=headers, params=params)
    elif method == "PUT":
        response = requests.put(api_url, auth=auth, headers=headers, params=params)
    else:
        raise UserWarning('GET or POST or PUT are the only supported request methods.')

    # If the response errored, raise for that.
    if response.status_code != requests.codes.ok:
        response.raise_for_status()

    if return_type == 'json':
        return response.json()
    else:
        return response


PyToggl._query = _query


def get_total_duration(data):
    prefix, entries = data
    return prefix, sum(e['duration'] for e in entries)


def split_description(group):
    description, entries = group
    parts = description.split(' ', 1)
    # Allow for descriptions without
    if len(parts) > 1:
        return parts, entries
    return (parts[0], ''), entries


def group_by_description(entries):
    """
    :param entries: entries from the Toggl API
    :return: list of two-tuples: the description, and the list of entries for the day
    """
    ret = defaultdict(list)
    for e in entries:
        ret[e['description']].append(e)
    return sorted(ret.items())


def group_by_day(entries):
    """
    :param entries: entries from the Toggl API
    :return: list of two-tuples: the day, and the list of entries for the day
    """


def total_duration(entries):
    return sum(e['duration'] for e in entries)


def log_invalid_entries(invalid_entries):
    """
    *********
    * Invalid Description *
    :param invalid_entries:
    :return:
    """
    invalid_entries = [(err, val) for (val, err) in invalid_entries]
    errs = defaultdict(list)
    for err, val in invalid_entries:
        errs[err].append(val)

    # to_log = list()
    # for err, entries in errs.iteritems():
    #     to_log.append('\n'.join(['%s : %s' % (err, entry.get('description', entry.get('id', '--'))) for entry in entries]))
    #
    # print '\n*********\n'
    # print '\n\n'.join(to_log)
    # print '\n*********\n'


    for err, entries in errs.iteritems():
        l = len(err)
        print
        print bcolors.bold(bcolors.underline(err))
        # print bcolors.UNDERLINE + err, '\n'
        # print
        # border = '*' * (len(err) + 4)

        # print '\n' + border + '\n* ' + str(err) + ' *\n' + border + '\n'
        print '\n'.join(map(str, [e.get('description', e['id']) for e in entries]))
        print


def split(m_entries):
    valid_entries = filter(has_no_error, m_entries)
    invalid_entries = filter(has_error, m_entries)

    return map(get_val, valid_entries), invalid_entries


def main():
    # toggl = PyToggl(settings.TOGGL_API_TOKEN)
    # jira = JIRA()
    # entries = toggl.query('/time_entries')
    entries = get_entries()
    m_entries = map(validate_one, entries)

    valid_entries, invalid_entries = split(m_entries)

    log_invalid_entries(invalid_entries)

    print bcolors.header(bcolors.underline('\nLogging to Jira\n'))

    groups = group_by_description(valid_entries)
    cleaned = map(split_description, groups)

    for (issue, comment), entries in cleaned:
        print (bcolors.bold('%-8s') + ' %s') % (
            timedelta(seconds=total_duration(entries)), bcolors.okblue(issue) + ' ' + comment), [e['id'] for e in
                                                                                                 entries]
        # toggl.query('/')

    summed = map(get_total_duration, cleaned)

    entry_ids = ','.join(map(str, [e['id'] for e in valid_entries]))
    # toggl.query('/time_entries/%s' % entry_ids, )






    # jira.add_worklog('SARR-128', timeSpentSeconds=60, comment='Test!')
