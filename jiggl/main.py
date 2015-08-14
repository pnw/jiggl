import json
import os
from datetime import timedelta, datetime
from jira import JIRAError
from sources.ji import ensure_open_ticket, add_worklog
from clean import split_entries
import curried_toolz as z
from display.basic import print_invalid_entries, print_valid_entries, print_total_for_day, print_jira_preflight, \
    print_jira_postflight, print_welcome_for_date
from jiggl.utils import clear_screen, get_val
from jiggl.colors import bcolors
from logger import record_worklog
from model import to_tce

# https://docs.atlassian.com/jira/REST/ondemand/#api/2/issueLink-linkIssues
from sources.ggl import get_end_for_date, get_start_for_date, JIGGLD_TAG
from jiggl.globs import toggl


def get_entries():
    current_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_path, 'fixtures', 'entries.json')) as f:
        return json.load(f)



# TODO: Add records in a sensible fashion instead of a giant json file. Maybe sqlite?

def replace_cologne(entry):
    entry['description'] = entry.get('description', '').replace(': ', ' ').replace(':', ' ')
    return entry


def for_day(dt):
    print_welcome_for_date(dt)
    entries = toggl.query('/time_entries', params={'start_date': get_start_for_date(dt),
                                                   'end_date': get_end_for_date(dt)})

    entries = z.map(replace_cologne, entries)

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

    if raw_input('\nLog time? (Y/n) ') not in ('Y', 'y', ''):
        print bcolors.fail('Will not log time. Exiting')
        exit()

    print

    logged_entries = []  # the tickets on Toggl that need to be marked as jiggld

    tces = z.groupby(lambda tce: tce.ticket, z.map(to_tce, valid_entries))
    try:
        for ticked_id, tces in tces.iteritems():
            for tce in tces:
                print_jira_preflight(tce)
                with ensure_open_ticket(ticked_id):
                    # continue
                    try:
                        worklog = add_worklog(tce)
                    except JIRAError as e:
                        if 'non-editable workflow state' in str(e):
                            print bcolors.fail('CANNOT EDIT!')
                            exit()
                        print bcolors.fail(str(e))
                        continue
                    # print tce.entry['id']
                    logged_entries.append(tce.entry)
                    print 'WORKLOG ID', worklog.id
                    record_worklog(tce, worklog.id)
                    print_jira_postflight(tce, None)

                    # if raw_input('Good?') != '':
                    #     print bcolors.fail('Exiting')
                    #     exit()
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
