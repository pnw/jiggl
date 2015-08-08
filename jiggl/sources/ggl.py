from dateutil import parser as dtparser

from jiggl.globs import toggl
from jiggl.colors import bcolors
from jiggl import curried_toolz as z
from jiggl.monkey import REMOVE_TAG


def toggl_strptime(datestring):
    return dtparser.parse(datestring)


def get_end_for_date(dt):
    return '%sT23:59:00+12:00' % (dt.isoformat().split('T')[0])


def get_start_for_date(dt):
    # can pass a datetime or date
    return '%sT00:00:00+12:00' % (dt.isoformat().split('T')[0])


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


JIGGLD_TAG = 'jiggld'
