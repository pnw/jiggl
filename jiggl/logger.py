from datetime import datetime
import json
import os
import settings


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


logfile = settings.records_filepath