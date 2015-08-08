from datetime import datetime
import logging
from cliff.command import Command
from jiggl import main
from jiggl.commands.base import BaseLogCommand


class LogSince(BaseLogCommand):
    """jiggl log since 2015-10-12
    logs from now since the provided date"""


class LogWeek(BaseLogCommand):
    """Logs the week of the day provided"""


class LogDates(BaseLogCommand):
    """Logs from `from_date` until `to_date`"""


class LogToday(BaseLogCommand):
    """Just logs today"""


class SimpleLog(Command):
    "A simple command that prints a message."

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SimpleLog, self).get_parser(prog_name)
        strpdate = lambda val: datetime.strptime(val, '%Y-%m-%d').date()
        parser.add_argument('day', nargs='?', default=datetime.now().date(), type=strpdate)
        return parser

    def take_action(self, parsed_args):
        main.for_day(parsed_args.day)

