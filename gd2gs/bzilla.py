""" Bugzilla access and operations """

import configparser
import os

from bugzilla import Bugzilla

import gd2gs.logger as log

# Error messages:
BUGZILLA_CONNECTION_FAILURE = 'failed to establish Bugzilla connection'
BUGZILLA_QUERY_FAILED = 'Bugzilla query failed'

class Bzilla:
    """ Bugzilla class """

    def __init__(self, bzilla_domain, bzilla_url, bzilla_api_key):
        """ Get bugzilla access using API key """
        log.debug('access Bugzilla')
        self.path = os.path.expanduser(bzilla_api_key)
        self.config = configparser.ConfigParser()
        self.config.read(self.path)
        Bugzilla.api_key = self.config.get(bzilla_domain, 'api_key')
        try:
            self.bzilla_access = Bugzilla(url=bzilla_url)
        except:    # pylint: disable=bare-except
            log.error(BUGZILLA_CONNECTION_FAILURE)
        log.debug('access Bugzilla - successful')

#    def __str__(self):
#        return str(self.__class__) + ": " + str(self.__dict__)

    def get_data(self, query):
        """ Query to Bugzilla """
        log.debug('Bugzilla query: ' + str(query))
        try:
            data = self.bzilla_access.query(query)
        except:    # pylint: disable=bare-except
            self.bzilla_logout()
            log.fatal_error(BUGZILLA_QUERY_FAILED)
        return data

    def bzilla_logout(self):
        """ Bugzilla logout """
        self.bzilla_access.logout()
