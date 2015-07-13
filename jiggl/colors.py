class _bcolors(object):
    """
    http://stackoverflow.com/a/287944/1787372
    ANSI escape sequences to bring color to the dreary world of the command line

    Example:
    >>> print bcolors.header('I am a header')
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def wraps(self, color, s):
        """
        Takes care of the boiler plate of printing a colored string and including the end-code.

        :param color: A ANSI color prefix
        :param s: Any string to print
        """
        return '%s%s%s' % (color, s, self.ENDC)

    def header(self, s): return self.wraps(self.HEADER, s)

    def okblue(self, s): return self.wraps(self.OKBLUE, s)

    def okgreen(self, s): return self.wraps(self.OKGREEN, s)

    def warning(self, s): return self.wraps(self.WARNING, s)

    def fail(self, s): return self.wraps(self.FAIL, s)

    def endc(self, s): return self.wraps(self.ENDC, s)

    def bold(self, s): return self.wraps(self.BOLD, s)

    def underline(self, s): return self.wraps(self.UNDERLINE, s)

    __all__ = (header, okblue)


bcolors = _bcolors()
