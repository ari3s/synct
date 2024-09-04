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


synct.gitlab: GitLab access and operations
"""

import os
import requests

import synct.logger as log

TIMEOUT = 10    # in seconds

# Debug messages:
GET_GITLAB_TOKEN = 'get GitLab token'
GITLAB_QUERY = 'GitLab query: '

# Error messages:
GITLAB_QUERY_FAILED = 'GitLab query failed in the configuration file for the sheet '
ERROR = 'error'

# Warning messages:
INCOMPLETE_RESULTS = 'incomplete_results'

class Gitlab:
    """ GitLab class """

    def __init__(self, url, token_file_name):
        """ Get GitLab access using API key """
        self.get_token(token_file_name)
        self.url = url

    def data_query(self, sheet, query):
        """ Query to GitLab with paging """
        request = self.url + query
        response_list = []
        while len(request) > 0:
            log.debug(GITLAB_QUERY + request)
            try:
                response = requests.get(request, headers=self.headers, timeout=TIMEOUT)
            except (AttributeError, TypeError) as exception:
                log.error(GITLAB_QUERY_FAILED + sheet + ':\n' + request)
                log.fatal_error(exception)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exception:
                log.error(GITLAB_QUERY_FAILED + sheet + ':\n' + request)
                log.fatal_error(exception)
            if not response.ok:
                log.warning(INCOMPLETE_RESULTS)
            resp = response.json()
            if ERROR in resp:
                log.error(ERROR + ': '+ str(resp[ERROR]))
                break
            response_list.extend(resp)
            request = find_between(response.headers['link'], '<', '>; rel="next"')
        return response_list

    def get_token(self, token_file_name):
        """ Get token from the file """
        token = None
        if token_file_name:
            log.debug(GET_GITLAB_TOKEN)
            try:
                with open(os.path.expanduser(token_file_name), 'r', encoding="utf8") as token_file:
                    token = token_file.read().rstrip('\n')
                    token_file.close()
            except OSError as exception:    #pylint: disable=duplicate-code
                log.error(exception)
        if token:
            self.headers = {'PRIVATE-TOKEN': token}
        else:
            self.headers = None

def find_between(string, first_string, last_string):
    """ Get substring between two strings """
    try:
        end = string.index(last_string)
        string = string[:end]
        start = string.rindex(first_string) + len(first_string)
        return string[start:]
    except ValueError:
        return ''
