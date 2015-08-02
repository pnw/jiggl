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



def split_description(group):
    description, entries = group
    parts = description.split(' ', 1)
    # Allow for descriptions with a Jira task identifier but no accomanying description
    if len(parts) > 1:
        return parts, entries
    return (parts[0], ''), entries


def print_error_group((err, entries)):
    print
    print bcolors.bold(bcolors.underline(err))
    print '\n'.join(map(str, [e.get('description', e['id']) for e in entries]))
    print


print_invalid_entries = z.compose(
    z.map(print_error_group),
    iteritems,
    z.valmap(z.map(get_val)),
    z.groupby(get_error),
)

get_valid_invalid = z.get([False, True], default=[])
group_by_has_error = z.groupby(has_error)

split_entries = z.compose(
    get_valid_invalid,
    group_by_has_error,
    validate_many,
)

total_duration = z.compose(sum, z.pluck('duration', default=0))

sum_as_timedelta = lambda entries: timedelta(seconds=total_duration(entries))

def print_valid_entries(entries):
    print bcolors.header(bcolors.underline('\nLogging to Jira\n'))

    # entries = map(get_val, entries)

    groups = z.groupby(z.get('description', default=''), entries)
    cleaned = map(split_description, groups.iteritems())


    for (issue, comment), es in cleaned:
        print (bcolors.bold('%-8s') + ' %s') % (sum_as_timedelta(es), bcolors.okblue(issue) + ' ' + comment)
    # entry_ids = ','.join(map(str, [e['id'] for e in entries]))


def print_total_for_day(entries):
    print '-------'
    print (bcolors.bold('%-8s') + ' Total Time to log for day') % (sum_as_timedelta(entries))



def make_two_digits(val):
    val = str(val)
    if len(val) == 1:
        val = '0' + val
    return val

def clean_ymd(year, month, day):
    year = str(year)
    assert len(year) == 4
    month = make_two_digits(month)
    day = make_two_digits(day)
    return year, month, day

def get_start_for_date(year, month, day):
    year, month, day = clean_ymd(year, month, day)
    return '%s-%s-%sT00:00:00+11:30' % (year, month, day)

def get_end_for_date(year, month, day):
    year, month, day = clean_ymd(year, month, day)
    return '%s-%s-%sT23:59:00+11:30' % (year, month, day)



def main():
    toggl = PyToggl(settings.TOGGL_API_TOKEN)
    # jira = JIRA()

    year = '2015'
    month = '07'
    def for_day(day):
        try:
            entries = toggl.query('/time_entries', params={'start_date': get_start_for_date(year, month, day), 'end_date': get_end_for_date(year, month, day)})
        except Exception as e:
            print bcolors.fail(e.response.text)
            exit()

        valid_entries, invalid_entries = split_entries(entries)

        print 'Logging for day', get_start_for_date(year, month, day).split('T')[0]
        print_invalid_entries(invalid_entries)

        valid_entries = list(z.map(get_val, valid_entries))

        print_valid_entries(valid_entries)
        print_total_for_day(valid_entries)

    for d in range(1, 31):
       for_day(d)
       raw_input('\nContinue?')

    #






    # jira.add_worklog('SARR-128', timeSpentSeconds=60, comment='Test!')


if __name__ == '__main__':
    clear_screen()
    main()
