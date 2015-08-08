"""
Jiggl globals
Named "globs" because global and globals are reserved python keywords
"""
from jira import JIRA
from monkey import Toggl
import settings


class Jiggl(object):
    def __init__(self):
        self.toggl = Toggl(settings.TOGGL_API_TOKEN)

    _jira = None

    @property
    def jira(self):
        """
        Lazy-load the JIRA client, because it makes a bunch of requests when you instantiate the class
        because that's cool to do right?
        :rtype: JIRA
        """
        if not self._jira:
            self._jira = JIRA(server=settings.JIRA_URL, basic_auth=(settings.JIRA_USERNAME, settings.JIRA_PASSWORD))
        return self._jira




jiggl = Jiggl()
toggl = jiggl.toggl
jira = jiggl.jira
