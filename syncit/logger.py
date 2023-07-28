""" Logging handling """

import logging
import os
import sys

# Debug messages:
SCRIPT_TERMINATED = 'script terminated'

log = logging.getLogger(os.path.basename(sys.argv[0]))

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
    global e_flag                   # pylint: disable=invalid-name, global-variable-undefined
    e_flag = False                  # error flag

def fatal_error(error_message):
    """ Report the error and terminate as failed """
    log.error(error_message)
    log.debug(SCRIPT_TERMINATED)
    sys.exit(1)

def check_error():
    """ If error flag is set then teminate the script """
    global e_flag                   # pylint: disable=invalid-name, global-variable-not-assigned
    if e_flag:
        log.debug(SCRIPT_TERMINATED)
        sys.exit(1)

def error(error_message):
    """ Report the error and terminate as failed """
    global e_flag                   # pylint: disable=invalid-name, global-variable-undefined
    e_flag = True                   # set error flag
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
