from collections import namedtuple
import json
import os

from datetime import timedelta, datetime
from jira import JIRA
from jira.utils import JIRAError
from clean import JIGGLD_TAG
import curried_toolz as z
from toolz.compatibility import iteritems
from dateutil import parser as dtparser

from jiggl.clean import validate_many
from jiggl.monkey import Toggl
from jiggl.utils import has_error, clear_screen, get_error, get_val
from jiggl import settings
from jiggl.colors import bcolors

# PyToggl = monkey_pytoggl(PyToggl)
from monkey import REMOVE_TAG


def get_entries():
    current_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_path, 'fixtures', 'entries.json')) as f:
        return json.load(f)


class Jiggl(object):
    def __init__(self):
        self.toggl = Toggl(settings.TOGGL_API_TOKEN)

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


def _split_description(description):
    parts = description.split(' ', 1)
    if len(parts) > 1:
        return tuple(parts)
    return description, ''


def print_error_group((err, entries)):
    print
    print bcolors.bold(bcolors.underline(err))
    print '\n'.join(map(str, [e.get('description', e['id']) for e in entries]))
    print


def _log(key, l):
    return l


log = z.curry(_log)

print_invalid_entries = z.compose(
    list,
    log('final'),
    z.map(print_error_group),
    log('iteritems'),
    iteritems,
    log('valmap'),
    z.valmap(z.map(get_val)),
    log('groupby'),
    z.groupby(get_error),
    log('initital')
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


def print_total_for_day(entries):
    print '-------'
    print (bcolors.bold('%-8s') + ' Total Time to log for day') % (sum_as_timedelta(entries))


TicketCommentEntry = namedtuple('TicketCommentEntry', ['ticket', 'comment', 'entry'])


def to_tce(entry):
    ticket, comment = _split_description(z.get('description', entry))
    return TicketCommentEntry(ticket, comment, entry)


def prep_comment_for_jira(tce):
    comment = '%s |togglid:%s|' % (tce.comment, tce.entry['id'])
    return TicketCommentEntry(tce.ticket, comment, tce.entry)


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
    return '%s-%s-%sT00:00:00+12:00' % (year, month, day)


def get_end_for_date(year, month, day):
    year, month, day = clean_ymd(year, month, day)
    return '%s-%s-%sT23:59:00+12:00' % (year, month, day)


def toggl_strptime(datestring):
    return dtparser.parse(datestring)


def jira_strftime(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S.000%z')


toggl_to_jira_datefmt = z.compose(
    jira_strftime,
    toggl_strptime,
)


def print_jira_preflight(tce):
    start, duration = z.get(['start', 'duration'], tce.entry)
    print bcolors.header('Adding Jira worklog:'), \
        'start(%s)' % bcolors.okblue(start.split('T')[-1].split('+')[0]), \
        'duration(%s)' % bcolors.okblue(timedelta(seconds=duration)),
    print bcolors.okblue(tce.ticket), tce.comment,
    print '...',


def print_jira_postflight(tce, response):
    print bcolors.okgreen(' Success!')


def print_welcome_for_date(date):
    s = '\n************************************\n'
    s += '* Logging for day: %s *' % date.ctime().replace('00:00:00 ', '')
    s += '\n************************************\n'
    print bcolors.warning(s)


def main():
    jiggl = Jiggl()
    toggl = jiggl.toggl
    jira = jiggl.jira

    year = 2015
    month = 07

    def clear_all_tags(day):
        print 'Clearing tags for day', day,
        entries = toggl.query('/time_entries', params={'start_date': get_start_for_date(year, month, day),
                                                       'end_date': get_end_for_date(year, month, day)})

        # entries = z.filter(lambda e: JIGGLD_TAG in z.get('tags', e, []), entries)
        ids = list(z.pluck('id', entries))
        tags = list(z.pluck('tags', entries, default=[]))
        print tags, bcolors.okblue('-->'),
        if not ids or not any(tags):
            print bcolors.okblue('No tags to clear')
        else:
            resp = toggl.update_tags(ids, [JIGGLD_TAG, 'jiggggld'], REMOVE_TAG)
            print list(z.pluck('tags', resp['data'], default=[]))

    def for_day(day):

        print_welcome_for_date(datetime(year, month, day))
        entries = toggl.query('/time_entries', params={'start_date': get_start_for_date(year, month, day),
                                                       'end_date': get_end_for_date(year, month, day)})

        valid_entries, invalid_entries = split_entries(entries)

        print_invalid_entries(invalid_entries)
        valid_entries = list(z.map(get_val, valid_entries))
        if len(valid_entries) == 0:
            print bcolors.okblue('No time entries to log for today')
            if not raw_input('\nContinue? (Y/n)') in ('Y', 'y', ''):
                exit()
            return

        print_valid_entries(valid_entries)
        print_total_for_day(valid_entries)

        if raw_input('\nLog time? (Y/n)') not in ('Y', 'y', ''):
            print bcolors.fail('Will not log time. Exiting')
            exit()

        print

        logged_entries = []  # the tickets on Toggl that need to be marked as jiggld

        try:
            for tce in z.map(z.compose(prep_comment_for_jira, to_tce), valid_entries):
                print_jira_preflight(tce)

                print_jira_postflight(tce, None)

                logged_entries.append(tce.entry)
        except JIRAError as e:
            print bcolors.fail(str(e))
        except Exception as e:
            print bcolors.fail(str(e))
        finally:
            if logged_entries:
                print 'Marking %s Toggl entries as tagged' % (len(logged_entries))
                resp = toggl.update_tags(list(z.pluck('id', logged_entries)), [JIGGLD_TAG])
            else:
                print 'No Toggl entries to tag as jiggld'

    for d in range(1, 31):
        for_day(d)
        # clear_all_tags(d)

    exit()
    jira.add_worklog('SARR-128', timeSpentSeconds=60, comment='Test!')


if __name__ == '__main__':
    clear_screen()
    main()
