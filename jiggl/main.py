from collections import namedtuple
from contextlib import contextmanager
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


# https://docs.atlassian.com/jira/REST/ondemand/#api/2/issueLink-linkIssues


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

jiggl = Jiggl()
toggl = jiggl.toggl
jira = jiggl.jira


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


def get_start_for_date(dt):
    # can pass a datetime or date
    return '%sT00:00:00+12:00' % (dt.isoformat().split('T')[0])


def get_end_for_date(dt):
    return '%sT23:59:00+12:00' % (dt.isoformat().split('T')[0])


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

OPEN = "1"  # "Open"
IN_PROGRESS = "3"  # "In Progress"
REOPENED = "4"  # "Reopened"
VERIFICATION = "5"  # "Verification / Testing"
COMPLETE = "6"  # "Complete / Done"
DONE = "10100"  # "Done"
IN_REVIEW = "10101"  # "In Review"
TO_DO = "10102"  # "To Do"
VERIFIED = "10200"  # "Verified / Ready to Deploy"


def _get_transition_id(status, ticket):
    """

    :param status:
    :param ticket:
    :return:
    """
    raw_transitions = jira.transitions(ticket)
    transitions = list(z.filter(lambda transition: z.get_in(['to', 'id'], transition) == status, raw_transitions))
    assert len(transitions) == 1
    return transitions[0]['id']

get_transition_id = z.curry(_get_transition_id)
reopen_transition = get_transition_id(REOPENED)

def add_worklog(tce):
    def log():
        started = toggl_strptime(tce.entry['start'])
        return jira.add_worklog(
            tce.ticket,
            timeSpentSeconds=tce.entry['duration'],
            comment=tce.comment,
            started=started,
        )

    try:
        worklog = log()
    except JIRAError as e:
        ticket = jira.issue(tce.ticket)

        status_id = ticket.fields.status.id
        if status_id != COMPLETE:
            print bcolors.fail('Invalid status %s' % status_id)
            raise

        reclose_transition = get_transition_id(status_id)

        jira.transition_issue(ticket, reopen_transition(ticket))
        worklog = log()
        jira.transition_issue(ticket, reclose_transition(ticket))
    return worklog

@contextmanager
def ensure_open_ticket(ticket_id):
    """
    Allows us to reopen a ticket once, and log against it a bunch of times.
    :param ticket_id:
    :return:
    """
    # TODO: This gives race conditions if someone updates a ticket while we are logging time.
    ticket = jira.issue(ticket_id)
    status_id = ticket.fields.status.id

    if status_id == COMPLETE:
        reclose_transition = get_transition_id(status_id)
        jira.transition_issue(ticket, reopen_transition(ticket))
        print bcolors.warning('Reopening ticket')
        try:
            yield
        finally:
            print bcolors.warning('Reclosing ticket')
            jira.transition_issue(ticket, reclose_transition(ticket))
    else:
        # ticket is in a mutable state on jira, so we can just log away
        yield



logfile = settings.records_filepath

# TODO: Add records in a sensible fashion instead of a giant json file. Maybe sqlite?
def get_records():
    """
    Records are stored as a hash:
        {
            "<toggl_id>": {
                "jira_ticket": "SARR-156",
                "worklog_id": "<jira_id>",
                "logged": "<datetime>"
            },
        }
    :return:
    """
    if not os.path.isfile(logfile):
        print 'Creating logfile'
        with open(logfile, 'w') as fo:
            json.dump({}, fo)

    with open(logfile) as f:
        return json.load(f)

def save_records(records):
    with open(logfile, 'w') as fo:
        json.dump(records, fo, indent=2)

def record_worklog(tce, worklog_id):
    """
    :param tce:
    :type tce: TicketCommentEntry
    :param worklog: jira.resources.Worklog
    :return:
    """
    records = get_records()
    if tce.ticket in records:
        raise Exception('This Toggl entry already has a jira worklog entry')
    records[tce.entry['id']] = {
        'jira_ticket': tce.ticket,
        'worklog_id': worklog_id,
        'logged': datetime.utcnow().isoformat()
    }
    save_records(records)


def main():

    # print jira.add_worklog('SARR-156', timeSpentSeconds=60, comment='Test!')
    # exit()

    #
    # t = TicketCommentEntry('SARR-156', 'test', {'duration': 122})
    # add_worklog(t)
    # exit()


    def clear_all_tags(dt):
        print 'Clearing tags for day', dt.isoformat(),
        entries = toggl.query('/time_entries', params={'start_date': get_start_for_date(dt),
                                                       'end_date': get_end_for_date(dt)})

        # entries = z.filter(lambda e: JIGGLD_TAG in z.get('tags', e, []), entries)
        ids = list(z.pluck('id', entries))
        tags = list(z.pluck('tags', entries, default=[]))
        print tags, bcolors.okblue('-->'),
        if not ids or not any(tags):
            print bcolors.okblue('No tags to clear')
        else:
            resp = toggl.update_tags(ids, [JIGGLD_TAG, 'jiggggld'], REMOVE_TAG)
            print list(z.pluck('tags', resp['data'], default=[]))

    def for_day(dt):

        print_welcome_for_date(dt)
        entries = toggl.query('/time_entries', params={'start_date': get_start_for_date(dt),
                                                       'end_date': get_end_for_date(dt)})

        valid_entries, invalid_entries = split_entries(entries)

        print_invalid_entries(invalid_entries)
        valid_entries = list(z.map(get_val, valid_entries))
        if len(valid_entries) == 0:
            print bcolors.okblue('No time entries to log for today')
            # if not raw_input('\nContinue? (Y/n)') in ('Y', 'y', ''):
            #     exit()
            return

        print_valid_entries(valid_entries)
        print_total_for_day(valid_entries)

        # if raw_input('\nLog time? (Y/n)') not in ('Y', 'y', ''):
        #     print bcolors.fail('Will not log time. Exiting')
        #     exit()

        print

        logged_entries = []  # the tickets on Toggl that need to be marked as jiggld

        tces = z.groupby(lambda tce: tce.ticket, z.map(to_tce, valid_entries))
        try:
            for ticked_id, tces in tces.iteritems():
                for tce in tces:

                    print_jira_preflight(tce)

                    with ensure_open_ticket(ticked_id):
                        worklog = add_worklog(tce)
                        logged_entries.append(tce.entry)
                        # print 'WORKLOG ID', worklog.id
                        record_worklog(tce, worklog.id)
                        print_jira_postflight(tce, None)

                    # if raw_input('Good?') != '':
                    #     print bcolors.fail('Exiting')
                    #     exit()

        except JIRAError as e:
            if 'non-edi1table workflow state' in str(e):
                print bcolors.fail('CANNOT EDIT!')
                exit()
            print bcolors.fail(str(e))
            raise
        except Exception as e:
            print bcolors.fail(str(e))
            raise
        finally:
            if logged_entries:
                print 'Marking %s Toggl entries as tagged' % (len(logged_entries))
                resp = toggl.update_tags(list(z.pluck('id', logged_entries)), [JIGGLD_TAG])
            else:
                print 'No Toggl entries to tag as jiggld'

    for_day((datetime.now() - timedelta(days=1)).date())
    # for_day(31)
    # for d in range(1, 4 + 1):
    #     for_day(d)
        # clear_all_tags(d)

    exit()


if __name__ == '__main__':
    clear_screen()
    main()
