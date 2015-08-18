import json
import os

jiggldir = os.path.join(os.path.expanduser('~'), '.jiggl')
settings_filepath = os.path.join(jiggldir, '.auth')
records_filepath = os.path.join(jiggldir, 'records.json')

project_path = os.path.dirname(os.path.realpath(__file__))


if os.path.lexists(settings_filepath):
    with open(settings_filepath) as f:
        config = json.load(f)
else:
    config = {}


TOGGL_API_TOKEN = config.get('toggl_api_token', '')
JIRA_USERNAME = config.get('jira_username', '')
JIRA_PASSWORD = config.get('jira_password', '')
JIRA_URL = config.get('jira_url', '')

