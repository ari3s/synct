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


synct.logger: Logging handling
"""

import logging
import os
import sys

# Debug messages:
SCRIPT_TERMINATED = 'script terminated'

log = logging.getLogger(os.path.basename(sys.argv[0]))

class ErrorFlag:
    """ Error flag handling """
    def __init__(self):
        """ Set the initial error flag value """
        self._error_flag = False

    def set(self):
        """ Set the error flag """
        self._error_flag = True

    def check(self):
        """ Check the error flag """
        return self._error_flag

ERROR_FLAG = ErrorFlag()        # Define the error flag

def setup(verbosity):
    """ Transform the verbosity from CLI to logging level """
    base_loglevel = 30
    verbosity = min(verbosity, 2)
    loglevel = base_loglevel - (verbosity * 10)
    logging.basicConfig(level=loglevel, format='%(name)s: %(levelname)s: %(message)s')
    logging.addLevelName(logging.ERROR, 'error')
    logging.addLevelName(logging.WARNING, 'warning')
    logging.addLevelName(logging.INFO, 'info')
    logging.addLevelName(logging.DEBUG, 'debug')

def fatal_error(error_message):
    """ Report the error and terminate as failed """
    log.error(error_message)
    log.debug(SCRIPT_TERMINATED)
    sys.exit(1)

def check_error():
    """ If error flag is set then teminate the script """
    if ERROR_FLAG.check():
        log.debug(SCRIPT_TERMINATED)
        sys.exit(1)

def error(error_message):
    """ Report the error and terminate as failed """
    ERROR_FLAG.set()
    log.error(error_message)

def warning(warning_message):
    """ Report the warning """
    log.warning(warning_message)

def info(info_message):
    """ Report the info """
    log.info(info_message)

def debug(debug_message):
    """ Report the warning """
    log.debug(debug_message)

def debug_level():
    """ Check debug level """
    return logging.getLevelName(logging.root.level) == 'debug'
