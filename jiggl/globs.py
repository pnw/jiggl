"""
Jiggl globals
Named "globs" because global and globals are reserved python keywords
"""
from jira import JIRA
from monkey import Toggl
import settings

toggl = Toggl(settings.TOGGL_API_TOKEN)
jira = JIRA(server=settings.JIRA_URL, basic_auth=(settings.JIRA_USERNAME, settings.JIRA_PASSWORD))