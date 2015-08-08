from datetime import timedelta
from toolz.compatibility import iteritems
from jiggl.clean import split_description, sum_as_timedelta
from jiggl.colors import bcolors
from jiggl import curried_toolz as z
from jiggl.utils import get_val, get_error


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