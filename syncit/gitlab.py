""" GitLab access and operations """

import os
import requests

import syncit.logger as log

TIMEOUT = 10    # in seconds

# Debug messages:
GET_GITLAB_TOKEN = 'get GitLab token'
GITLAB_QUERY = 'GitLab query: '

# Error messages:
GITLAB_QUERY_FAILED = 'GitLab query failed in the configuration file for the sheet '
ERROR = 'error'

# Warning messages:
INCOMPLETE_RESULTS = 'incomplete_results'

class Gitlab:    # pylint: disable=too-few-public-methods
    """ GitLab class """

    def __init__(self, url, token_file_name):
        """ Get GitLab access using API key """
        token = None
        if token_file_name:
            log.debug(GET_GITLAB_TOKEN)
            try:
                with open(os.path.expanduser(token_file_name), 'r', encoding="utf8") as token_file:
                    token = token_file.read().rstrip('\n')
                    token_file.close()
            except OSError as exception:
                log.error(exception)
        self.url = url
        if token:
            self.headers = {'PRIVATE-TOKEN': token}
        else:
            self.headers = None

    def data_query(self, sheet, query):
        """ Query to GitLab """
        log.debug(GITLAB_QUERY + self.url + query)
        try:
            response = requests.get(self.url+query, headers=self.headers, timeout=TIMEOUT)
        except (AttributeError, TypeError) as exception:
            log.error(GITLAB_QUERY_FAILED + sheet + ':\n' + self.url + query)
            log.fatal_error(exception)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exception:
            log.error(GITLAB_QUERY_FAILED + sheet + ':\n' + self.url + query)
            log.fatal_error(exception)
        if not response.ok:
            log.warning(INCOMPLETE_RESULTS)
        resp = response.json()
        if ERROR in resp:
            log.error(ERROR + ': '+ str(resp[ERROR]))
        return resp
