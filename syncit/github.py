""" GitHub access and operations """

import os
import requests

import syncit.logger as log

INCOMPLETE_RESULTS = 'incomplete_results'
TOTAL_COUNT = 'total_count='
TOTAL_TIMEOUT = 10

# Debug messages:
ACCESS_GITHUB = 'access GitHub'
GET_GITHUB_TOKEN = 'get GitHub token'

#ACCESS_GITHUB_SUCCESSFUL = 'access GitHub - successful'
GITHUB_QUERY = 'GitHub query: '

# Error messages:
GITHUB_QUERY_FAILED = 'GitHub query failed in the configuration file for the sheet '

class Github:    # pylint: disable=too-few-public-methods
    """ GitHub class """

    def __init__(self, url, token_file_name):
        """ Get GitHub access using API key """
        token = None
        if token_file_name:
            log.debug(GET_GITHUB_TOKEN)
            try:
                with open(os.path.expanduser(token_file_name), 'r', encoding="utf8") as token_file:
                    token = token_file.read().rstrip('\n')
                    token_file.close()
            except OSError as exception:
                log.warning(exception)
        self.url = url
        if token:
            self.headers = {'Authorization': 'Token '+token}
        else:
            self.headers = None

    def data_query(self, sheet, query):
        """ Query to GitHub """
        log.debug(GITHUB_QUERY + self.url + query)
        try:
            response = requests.get(self.url+query, headers=self.headers, timeout=10) # 10 seconds
        except (AttributeError, TypeError) as exception:
            log.error(GITHUB_QUERY_FAILED + sheet + ':\n' + str(query))
            log.fatal_error(exception)
        except requests.exceptions.Timeout as exception:
            log.fatal_error(exception)
        if not response.ok:
            log.warning(INCOMPLETE_RESULTS)
        resp = response.json()
        log.debug(TOTAL_COUNT + str(resp['total_count']))
        return resp['items']
