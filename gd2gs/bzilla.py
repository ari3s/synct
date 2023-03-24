""" Bugzilla access and operations """

import configparser
import os

from bugzilla import Bugzilla

import gd2gs.logger as log

BUGZILLA_CONNECTION_FAILURE = 'failed to establish Bugzilla connection'
BUGZILLA_QUERY_FAILED = 'Bugzilla query failed'
BUGZILLA_GET_DATA_FAILURE = 'failed to get data from Bugzilla'

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

    def xget_data(self, bzilla_number):
        """ Get bugzilla data of the specific bug from Bugzilla """
        try:
            return self.bzilla_access.getbug(bzilla_number)
        except:    # pylint: disable=bare-except
            log.error(BUGZILLA_GET_DATA_FAILURE)
            return None

    def xquery(self, query_data):
        """ Query to Bugzilla """
        try:
            return self.bzilla_access.query(query_data)
        except:    # pylint: disable=bare-except
            log.error(BUGZILLA_GET_DATA_FAILURE)
            return None

    def xcollect_data(self, bug_numbers):
        """ Collect bugzilla data of the specific bug list from Bugzilla"""
        try:
            return self.bzilla_access.query({'query_format': 'advanced',
                'include_fields': ['_default', 'flags', 'external_bugs'],
                'bug_id': bug_numbers,
                'limit': '0'})
        except:    # pylint: disable=bare-except
            log.error(BUGZILLA_GET_DATA_FAILURE)
            return None

    def xfilter_data(self, products, components):
        """ Query to Bugzilla """
        try:
            return self.bzilla_access.query({'query_format': 'advanced',
                'include_fields': ['_default', 'flags', 'external_bugs'],
                'product': products,
                'component': components,
                'status': '__open__',
                'j_top': 'OR',
                'f1': 'priority',
                'o1': 'equals',
                'v1': 'urgent',
                'f2': 'priority',
                'o2': 'equals',
                'v2': 'high',
                'f3': 'bug_severity',
                'o3': 'equals',
                'v3': 'urgent',
                'f4': 'bug_severity',
                'o4': 'equals',
                'v4': 'high',
                'f5': 'external_bugzilla.description',
                'o5': 'substring',
                'v5': 'Red Hat Customer Portal', # CEE_KEYWORD
                'f6': 'cf_partner',
                'o6': 'regexp',
                'v6': '.*',
                'f7': 'keywords',
                'o7': 'casesubstring',
                'v7': 'Security', # SECURITY_KEYWORD
                'f8': 'cf_devel_whiteboard',
                'o8': 'anywordssubstr',
                'v8': 'category:modularity', # MODULARITY_KEYWORD
                'limit': '0'})
        except:    # pylint: disable=bare-except
            log.error(BUGZILLA_GET_DATA_FAILURE)
            return None

    def bzilla_logout(self):
        """ Bugzilla logout """
        self.bzilla_access.logout()
