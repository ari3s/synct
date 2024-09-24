"""
synct reads data and copies in Google or Excel spreadsheet.

    Copyright (C) 2023  Jan Beran <ari3s.git@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <https://www.gnu.org/licenses/>.


synct.jira: Jira access and operations
"""

import os

from jira import JIRA, JIRAError

import synct.logger as log

# Debug messages:
ACCESS_JIRA = 'access Jira'
GET_JIRA_TOKEN = 'get Jira token'
JIRA_QUERY = 'Jira query: '

# Error messages:
JIRA_AUTH_FAILED = 'Jira authorization failed'
JIRA_QUERY_FAILED = 'Jira query failed in the configuration file for the sheet '

class Jira:
    """ Jira class """

    def __init__(self, url, token_file_name, max_results):
        """ Access Jira """
        token = self.get_token(token_file_name)
        try:
            self.access = JIRA(options={'server': url}, token_auth=token)
            log.debug(ACCESS_JIRA)
        except (JIRAError, AttributeError):
            log.error(JIRA_AUTH_FAILED)
        self.max_results = max_results

    def data_query(self, sheet, query):
        """ Get data required from Jira server """
        log.debug(JIRA_QUERY + query)
        try:
            data = self.access.search_issues(jql_str=query, maxResults=self.max_results)
        except (JIRAError, AttributeError) as exception:
            self.access.close()
            log.error(JIRA_QUERY_FAILED + sheet + ':\n' + query)
            log.fatal_error(exception)
        return data

    def get_token(self, token_file_name):
        """ Get token from the file """
        log.debug(GET_JIRA_TOKEN)
        try:
            with open(os.path.expanduser(token_file_name), 'r', encoding='utf-8') as token_file:
                token = token_file.read().rstrip('\n')
        except OSError as exception:
            log.error(exception)
        return token
