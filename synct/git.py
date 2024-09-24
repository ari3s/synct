"""
synct reads data and copies in Google or Excel spreadsheet.

    Copyright (C) 2024 Jan Beran <ari3s.git@gmail.com>

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

synct.git: GitHub and GitLab access and operations
"""

import json
import os
import requests

import synct.logger as log

TIMEOUT = 10    # in seconds
ERROR = 'error'

# Debug messages:
GET_GIT_TOKEN = ': get token'
GIT_QUERY = ' query: '
GIT_RESPONSE_HEADERS = ' response headers: '

# Error messages:
GIT_QUERY_FAILED = ': query failed in the configuration file for the sheet '
FATAL_ERROR = ': fatal error'

# Warning messages:
GIT_INCOMPLETE_RESULTS = ': incomplete_results'

class Git:
    """ Git class """

    def __init__(self, url):
        """ Get Git access using API key """
        self.git = None
        self.headers = None
        self.link = None
        self.url = url

    def get_token(self, token_file_name):
        """ Get token from the file """
        token = None
        if token_file_name:
            log.debug(self.git + GET_GIT_TOKEN)
            try:
                with open(os.path.expanduser(token_file_name), 'r', encoding='utf-8') as token_file:
                    token = token_file.read().rstrip('\n')
                    token_file.close()
            except OSError as exception:    #pylint: disable=duplicate-code
                log.error(self.git + ': ' + exception)
        return token

    def data_query(self, sheet, query):
        """ Query to Git with paging """
        request = self.url + query
        response_list = []
        while len(request) > 0:
            log.debug(self.git + GIT_QUERY + request)
            try:
                response = requests.get(request, headers=self.headers, timeout=TIMEOUT)
            except (AttributeError, TypeError, requests.RequestException) as exception:
                log.error(exception)
                log.error(self.git + GIT_QUERY_FAILED + sheet + ': ' + request)
            log.debug(self.git + GIT_RESPONSE_HEADERS + str(response.headers))
            if not response.ok:
                self.error_message(response)
            log.check_error()
            try:
                response_list.extend(self.data_response(response.json()))
                request = find_between(response.headers[self.link], '<', '>; rel="next"')
            except (KeyError, TypeError):
                log.error(self.git + GIT_QUERY_FAILED + sheet + ': ' + request)
            log.check_error()
        return response_list

    def data_response(self, resp):
        """ Git data response """

    def error_message(self, resp):
        """ Git error message output """

class Github(Git):
    """ GitHub class """

    def __init__(self, url, token_file_name):
        """ Get GitHub access using API key """
        Git.__init__(self, url)
        self.git = 'GitHub'
        self.link = 'Link'
        token = Git.get_token(self, token_file_name)
        self.headers = {'Authorization': 'Token ' + token} if token else ''

    def data_response(self, resp):
        """ GitHub data response """
        try:
            response = resp['items']
        except KeyError:
            log.fatal_error(self.git + FATAL_ERROR)
        return response

    def error_message(self, resp):
        """ GitHub error message output """
        initial_part = self.git + ' ' + ERROR + ': ' + str(resp.status_code) + ' '
        cont = json.loads(resp.text)
        log.error(initial_part + cont['message'])

class Gitlab(Git):
    """ GitLab class """

    def __init__(self, url, token_file_name):
        """ Get GitLab access using API key """
        Git.__init__(self, url)
        self.git = 'GitLab'
        self.link = 'link'
        token = Git.get_token(self, token_file_name)
        self.headers = {'PRIVATE-TOKEN': token} if token else ''

    def data_response(self, resp):
        """ GitLab data response """
        if ERROR in resp:
            log.error(self.git + ': '+ str(resp[ERROR]))
        return resp

    def error_message(self, resp):
        """ GitLab error message output """
        initial_part = self.git + ' ' + ERROR + ': '
        cont = json.loads(resp.text)
        try:
            msg = cont['error']
            try:
                msg = msg + '. ' + cont['error_description']
            except KeyError:
                pass
            initial_part = initial_part + str(resp.status_code) + ' '
        except KeyError:
            msg = cont['message']
        log.error(initial_part + msg)

def find_between(string, first_string, last_string):
    """ Get substring between two strings """
    try:
        end = string.index(last_string)
        string = string[:end]
        start = string.rindex(first_string) + len(first_string)
        return string[start:]
    except ValueError:
        return ''
