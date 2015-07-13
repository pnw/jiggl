import json
import os

settings_filepath = os.path.join(os.path.expanduser('~'), '.jiggl')

if os.path.lexists(settings_filepath):
    with open(settings_filepath) as f:
        config = json.load(f)
else:
    config = {}


TOGGL_API_TOKEN = config.get('toggl_api_token', '')
JIRA_USERNAME = config.get('jira_username', '')
JIRA_PASSWORD = config.get('jira_password', '')
JIRA_URL = config.get('jira_url', '')

