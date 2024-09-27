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


synct.bzilla: Bugzilla access and operations
"""

import configparser
import os

from bugzilla import Bugzilla

import synct.logger as log

API_KEY = 'api_key'
LIMIT = 'limit'
OFFSET = 'offset'

# Debug messages:
ACCESS_BUGZILLA = 'access Bugzilla'
ACCESS_BUGZILLA_SUCCESSFUL = 'access Bugzilla - successful'
BUGZILLA_QUERY = 'Bugzilla query: '

# Error messages:
BUGZILLA_CONNECTION_FAILURE = 'failed to establish Bugzilla connection'
BUGZILLA_QUERY_FAILED = 'Bugzilla query failed in the configuration file for the sheet '

class Bzilla:
    """ Bugzilla class """

    def __init__(self, bzilla_domain, bzilla_url, bzilla_api_key):
        """ Get bugzilla access using API key """
        log.debug(ACCESS_BUGZILLA)
        self.path = os.path.expanduser(bzilla_api_key)
        self.config = configparser.ConfigParser()
        self.config.read(self.path)
        try:
            Bugzilla.api_key = self.config.get(bzilla_domain, API_KEY)
            self.bzilla_access = Bugzilla(url=bzilla_url)
            log.debug(ACCESS_BUGZILLA_SUCCESSFUL)
        except configparser.Error as exception:
            log.error(exception)
            log.error(BUGZILLA_CONNECTION_FAILURE)

    def data_query(self, sheet, query):
        """ Query to Bugzilla with pagination """
        response_list = []
        if LIMIT in query:
            limit = query[LIMIT]
        else:
            limit = 0
            query[LIMIT] = limit
        while True:
            try:
                log.debug(BUGZILLA_QUERY + str(query))
                response = self.bzilla_access.query(query)
            except (AttributeError, TypeError) as exception:
                self.bzilla_logout()
                log.error(BUGZILLA_QUERY_FAILED + sheet + ':\n' + str(query))
                log.fatal_error(exception)
            if len(response) == 0:
                break                   # The query response is empty
            response_list.extend(response)
            if len(response) < limit:
                break                   # The query responded with less items than the page limit
            # Set next page query
            if OFFSET in query:
                query[OFFSET] = query[OFFSET] + len(response)
            else:
                query[OFFSET] = len(response)
        return response_list

    def bzilla_logout(self):
        """ Bugzilla logout """
        self.bzilla_access.logout()
