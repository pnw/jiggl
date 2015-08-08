import json
import os

from PyToggl.PyToggl import PyToggl
from cliff.command import Command
from requests.exceptions import HTTPError

from sources.jira import JIRA
from sources.jira import JIRAError
from jiggl.colors import bcolors
from jiggl.settings import settings_filepath
from utils import clear_screen


class Credentials(object):
    toggl_api_token = ''
    jira_username = ''
    jira_password = ''
    jira_url = ''

    def __init__(self):
        self.load()

    def load(self):
        """
        Loads any existing credentials onto the current object
        """
        if os.path.lexists(settings_filepath):
            with open(settings_filepath) as f:
                config = json.load(f)
                self.toggl_api_token = config.get('toggl_api_token', '')
                self.jira_username = config.get('jira_username', '')
                self.jira_password = config.get('jira_password', '')
                self.jira_url = config.get('jira_url', '')

    def persist(self):
        """
        Saves the credentials into a json file stored in the users homedirectory
        """
        with open(settings_filepath, 'w') as f:
            json.dump(self.__dict__, f, indent=4)

    def say_hi(self):
        clear_screen()
        print bcolors.header('Welcome to Jiggl!\n')
        print 'To use Jiggl, I\'ll need your credentials to both Jiggl and Toggl.\n' \
              'Your credentials will be stored in the file ' \
              'located at:\n\n' + bcolors.bold(settings_filepath)

    def say_goodbye(self):
        print bcolors.header('\nDone!')

    def check_toggl(self):
        """
        Make sure the user has entered a correct toggl token
        """
        print '\nChecking your Toggl credentials...'
        toggl = PyToggl(self.toggl_api_token)
        try:
            toggl.query('/me')
        except HTTPError:
            raise RuntimeError(bcolors.fail('Invalid Toggl API token.'))
        print bcolors.okblue('Success!')

    def check_jira(self):
        """
        Make sure the user has entered correct jira credentials
        """
        print '\nChecking your Jira credentials...'
        try:
            # Jira automatically does a credentials check when you instantiate the class
            JIRA(self.jira_url, basic_auth=(self.jira_username, self.jira_password))
        except JIRAError:
            raise RuntimeError(bcolors.fail('Invalid Jira credentials.'))
        print bcolors.okblue('Success!')

    def procure_toggl(self):
        print bcolors.header('\n\nToggl\n')
        print 'To read your Toggl feed, I just need an API token.\n' \
              'Your Toggl API token can be found at ' \
              'the bottom of your profile page:' \
              '\n\n' + bcolors.bold('https://www.toggl.com/app/profile') + '\n\n'

        if self.toggl_api_token:
            toggl_token = raw_input('Toggl token (enter to use existing): ')
        else:
            toggl_token = None
            while not toggl_token:
                toggl_token = raw_input('Toggl token: ')

        if toggl_token:
            self.toggl_api_token = toggl_token

    def procure_jira(self):
        print bcolors.header('\n\nJira\n')
        print 'To update your Jira tickets, I\'ll need three things:\n'
        print '1. Url (e.g. ' + bcolors.bold('http://jira.atlassian.net') + ')'
        print '2. Username ' + bcolors.warning('Note: Your Jira email will not work. You must provide your username.')
        print '3. Password\n'

        if self.jira_url:
            jira_url = raw_input('Jira Url (enter to use existing): ')
        else:
            jira_url = None
            while not jira_url:
                jira_url = raw_input('Jira Url; e.g. http://jira.atlassian.net: ')
        if jira_url:
            self.jira_url = jira_url

        if self.jira_username:
            jira_username = raw_input('Jira Username (enter to use existing): ')
        else:
            jira_username = None
            while not jira_username:
                jira_username = raw_input('Jira Username: ')
        if jira_username:
            self.jira_username = jira_username

        if self.jira_password:
            jira_password = raw_input('Jira Password (enter to use existing): ')
        else:
            jira_password = None
            while not jira_password:
                jira_password = raw_input('Jira Password: ')
        if jira_password:
            self.jira_password = jira_password

    def run(self):
        self.say_hi()

        self.procure_toggl()
        self.check_toggl()
        self.persist()

        self.procure_jira()
        self.check_jira()
        self.persist()

        self.say_goodbye()


class Login(Command):
    """
    Record the users credentials for authenticating with Jira and Toggle
    """

    def take_action(self, parsed_args):
        Credentials().run()
