from datetime import datetime
import logging
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


class SimpleLog(BaseLogCommand):
    "A simple command that prints a message."

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        main.for_day(datetime.now().date())

