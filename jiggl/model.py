from collections import namedtuple
from clean import _split_description
import curried_toolz as z

TicketCommentEntry = namedtuple('TicketCommentEntry', ['ticket', 'comment', 'entry'])


def to_tce(entry):
    ticket, comment = _split_description(z.get('description', entry))
    return TicketCommentEntry(ticket, comment, entry)