""" Bugzilla access and operations """

import configparser
import os

from bugzilla import Bugzilla

import syncit.logger as log

API_KEY = 'api_key'

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
        """ Query to Bugzilla """
        log.debug(BUGZILLA_QUERY + str(query))
        try:
            data = self.bzilla_access.query(query)
        except (AttributeError, TypeError) as exception:
            self.bzilla_logout()
            log.error(BUGZILLA_QUERY_FAILED + sheet + ':\n' + str(query))
            log.fatal_error(exception)
        return data

    def bzilla_logout(self):
        """ Bugzilla logout """
        self.bzilla_access.logout()
