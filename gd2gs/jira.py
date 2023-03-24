""" Jira class and operations """
import os

from jira import JIRA, JIRAError

import gd2gs.logger as log

JIRA_AUTH_FAILED = 'Jira authorization failed'
JIRA_QUERY_FAILED = 'Jira query failed'
MISSING_IN_THE_SPREADSHEET = 'missing in Google sheet'

class Jira:   # pylint: disable=too-few-public-methods
    """ Jira class """

    def __init__(self, url, token_file_name, max_results):
        """ Access Jira """
        log.debug('get Jira token')
        try:
            with open(os.path.expanduser(token_file_name), 'r') as token_file:
                token = token_file.read().rstrip('\n')
        except OSError as exception:
            log.error(exception)
        log.debug('access Jira')
        try:
            self.access = JIRA(options={'server': url}, token_auth=token)
        except (JIRAError, AttributeError):
            log.error(JIRA_AUTH_FAILED)
        self.max_results = max_results

    def get_data(self, query):
        """ Get data required from Jira server"""
        log.debug('Jira query: ' + query)
        try:
            data = self.access.search_issues(jql_str=query, maxResults=self.max_results)
        except (JIRAError, AttributeError):
            self.access.close()
            log.error(JIRA_QUERY_FAILED)
        return data
