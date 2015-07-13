from cliff.command import Command
import datetime


class BaseLogCommand(Command):
    """
    Base class for all logging operations.
    Purpose is to provide basic
    """

    def get_parser(self, prog_name):
        self.log.info(prog_name)
        parser = super(BaseLogCommand, self).get_parser(prog_name)
        strpdate = lambda val: datetime.datetime.strptime(val, '%Y-%m-%d').date()
        parser.add_argument('-d', '--days', dest='days', nargs='?', default=-1, type=int)
        parser.add_argument('-t', '--date_to', dest='date_to', nargs='?', default=None, type=strpdate)
        parser.add_argument('-f', '--date_from', dest='date_from', nargs='?', default=None, type=strpdate)
        return parser
