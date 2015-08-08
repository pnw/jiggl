import json
import os
from datetime import timedelta, datetime

from sources.jira import JIRAError
from sources.jira import JIRA, ensure_open_ticket, add_worklog, jira_strftime
from clean import JIGGLD_TAG
import curried_toolz as z
from display.basic import print_invalid_entries, print_valid_entries, print_total_for_day, print_jira_preflight, \
    print_jira_postflight, print_welcome_for_date
from jiggl.clean import validate_many
from jiggl.monkey import Toggl
from jiggl.utils import has_error, clear_screen, get_val
from jiggl import settings
from jiggl.colors import bcolors
from logging import record_worklog
from model import to_tce





# https://docs.atlassian.com/jira/REST/ondemand/#api/2/issueLink-linkIssues
from sources.toggl import toggl_strptime, get_end_for_date, get_start_for_date


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

get_valid_invalid = z.get([False, True], default=[])
group_by_has_error = z.groupby(has_error)

split_entries = z.compose(
    get_valid_invalid,
    group_by_has_error,
    validate_many,
)

total_duration = z.compose(sum, z.pluck('duration', default=0))

sum_as_timedelta = lambda entries: timedelta(seconds=total_duration(entries))

toggl_to_jira_datefmt = z.compose(
    jira_strftime,
    toggl_strptime,
)


# TODO: Add records in a sensible fashion instead of a giant json file. Maybe sqlite?


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
                continue
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


def main():
    # print jira.add_worklog('SARR-156', timeSpentSeconds=60, comment='Test!')
    # exit()

    #
    # t = TicketCommentEntry('SARR-156', 'test', {'duration': 122})
    # add_worklog(t)
    # exit()

    for_day((datetime.now() - timedelta(days=1)).date())
    # for_day(31)
    # for d in range(1, 4 + 1):
    #     for_day(d)
    # clear_all_tags(d)

    exit()


if __name__ == '__main__':
    clear_screen()
    main()
