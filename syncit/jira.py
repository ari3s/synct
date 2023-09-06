""" Jira class and operations """
import os

from jira import JIRA, JIRAError

import syncit.logger as log

# Debug messages:
ACCESS_JIRA = 'access Jira'
GET_JIRA_TOKEN = 'get Jira token'
JIRA_QUERY = 'Jira query: '

# Error messages:
JIRA_AUTH_FAILED = 'Jira authorization failed'
JIRA_QUERY_FAILED = 'Jira query failed in the configuration file for the sheet '

class Jira:   # pylint: disable=too-few-public-methods
    """ Jira class """

    def __init__(self, url, token_file_name, max_results):
        """ Access Jira """
        log.debug(GET_JIRA_TOKEN)
        try:
            with open(os.path.expanduser(token_file_name), 'r', encoding="utf8") as token_file:
                token = token_file.read().rstrip('\n')
        except OSError as exception:
            log.error(exception)
        try:
            self.access = JIRA(options={'server': url}, token_auth=token)
            log.debug(ACCESS_JIRA)
        except (JIRAError, AttributeError):
            log.error(JIRA_AUTH_FAILED)
        self.max_results = max_results

    def data_query(self, sheet, query):
        """ Get data required from Jira server"""
        log.debug(JIRA_QUERY + query)
        try:
            data = self.access.search_issues(jql_str=query, maxResults=self.max_results)
        except (JIRAError, AttributeError) as exception:
            self.access.close()
            log.error(JIRA_QUERY_FAILED + sheet + ':\n' + query)
            log.fatal_error(exception)
        return data
