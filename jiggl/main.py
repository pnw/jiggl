import json
import os

from PyToggl.PyToggl import PyToggl
from datetime import timedelta
from jira import JIRA
import curried_toolz as z
from toolz.compatibility import iteritems

from jiggl.clean import validate_many
from jiggl.monkey import monkey_pytoggl
from jiggl.utils import has_error, clear_screen
from jiggl import settings
from jiggl.colors import bcolors
from utils import get_error, get_val

PyToggl = monkey_pytoggl(PyToggl)


def get_entries():
    current_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_path, 'fixtures', 'entries.json')) as f:
        return json.load(f)


class Jiggl(object):
    def __init__(self):
        self.toggl = PyToggl(settings.TOGGL_API_TOKEN)

    _jira = None

    @property
    def jira(self):
        """
        Lazy-load the JIRA client, because it makes a bunch of requests when you instantiate the class
        because that's cool to do right?
        :rtype: JIRA
        """
        if not self._jira:
            self._jira = JIRA(server=settings.JIRA_URL, basic_auth=(settings.JIRA_USERNAME, settings.JIRA_PASSWORD))
        return self._jira


def get_total_duration(data):
    prefix, entries = data
    return prefix, sum(e['duration'] for e in entries)


def split_description(group):
    description, entries = group
    parts = description.split(' ', 1)
    # Allow for descriptions with a Jira task identifier but no accomanying description
    if len(parts) > 1:
        return parts, entries
    return (parts[0], ''), entries


get_duration = z.get('duration')
get_description = z.get('description', default='')


def print_error_group((err, entries)):
    print
    print bcolors.bold(bcolors.underline(err))
    print '\n'.join(map(str, [e.get('description', e['id']) for e in entries]))
    print


log_invalid_entries = z.compose(
    z.map(print_error_group),
    iteritems,
    z.valmap(z.map(get_val)),
    z.groupby(get_error),
)

get_valid_invalid = z.get([False, True])
group_by_has_error = z.groupby(has_error)

split_entries = z.compose(
    get_valid_invalid,
    group_by_has_error,
    validate_many,
)


def group_by_day(entries):
    """
    :param entries: entries from the Toggl API
    :return: list of two-tuples: the day, and the list of entries for the day
    """

def total_duration(entries):
    return sum(z.map(get_duration, entries))


def log_valid_entries(entries):
    print bcolors.header(bcolors.underline('\nLogging to Jira\n'))

    groups = z.groupby(get_description, entries)
    cleaned = map(split_description, groups)

    for (issue, comment), entries in cleaned:
        print (bcolors.bold('%-8s') + ' %s') % (
            timedelta(seconds=total_duration(entries)), bcolors.okblue(issue) + ' ' + comment), [e['id'] for e in
                                                                                                 entries]
        # toggl.query('/')

    summed = map(get_total_duration, cleaned)

    entry_ids = ','.join(map(str, [e['id'] for e in entries]))



def main():
    # toggl = PyToggl(settings.TOGGL_API_TOKEN)
    # jira = JIRA()
    # entries = toggl.query('/time_entries')
    entries = get_entries()

    valid_entries, invalid_entries = split_entries(entries)

    log_invalid_entries(invalid_entries)
    log_valid_entries(valid_entries)


    #






    # jira.add_worklog('SARR-128', timeSpentSeconds=60, comment='Test!')


if __name__ == '__main__':
    clear_screen()
    main()
