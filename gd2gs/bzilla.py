""" Bugzilla access and operations """

import configparser
import os

from bugzilla import Bugzilla

import gd2gs.logger as log

API_KEY = 'api_key'

# Debug messages:
ACCESS_BUGZILLA = 'access Bugzilla'
ACCESS_BUGZILLA_SUCCESSFUL = 'access Bugzilla - successful'
BUGZILLA_QUERY = 'Bugzilla query: '

# Error messages:
BUGZILLA_CONNECTION_FAILURE = 'failed to establish Bugzilla connection'
BUGZILLA_QUERY_FAILED = 'Bugzilla query failed'

class Bzilla:
    """ Bugzilla class """

    def __init__(self, bzilla_domain, bzilla_url, bzilla_api_key):
        """ Get bugzilla access using API key """
        log.debug(ACCESS_BUGZILLA)
        self.path = os.path.expanduser(bzilla_api_key)
        self.config = configparser.ConfigParser()
        self.config.read(self.path)
        Bugzilla.api_key = self.config.get(bzilla_domain, API_KEY)
        try:
            self.bzilla_access = Bugzilla(url=bzilla_url)
            log.debug(ACCESS_BUGZILLA_SUCCESSFUL)
        except:    # pylint: disable=bare-except
            log.error(BUGZILLA_CONNECTION_FAILURE)

#    def __str__(self):
#        return str(self.__class__) + ": " + str(self.__dict__)

    def get_data(self, query):
        """ Query to Bugzilla """
        log.debug(BUGZILLA_QUERY + str(query))
        try:
            data = self.bzilla_access.query(query)
        except:    # pylint: disable=bare-except
            self.bzilla_logout()
            log.error(BUGZILLA_QUERY_FAILED)
            data = None
        return data

    def bzilla_logout(self):
        """ Bugzilla logout """
        self.bzilla_access.logout()
