from contextlib import contextmanager
from jira import JIRAError
from jiggl.globs import jira
from jiggl.colors import bcolors
from jiggl import curried_toolz as z
from jiggl.sources.ggl import toggl_strptime


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


def jira_strftime(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S.000%z')
