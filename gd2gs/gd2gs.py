"""
gd2gs

The script gets data from the particular source and copies the data in Google
spreadsheet as it is defined in the config file.

usage: gd2gs [-h] [-c CONFIG] [-v] [-q] [-t]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        config file (default: gd2gs.yaml)
  -v, --verbose         verbose output (repeat for increased verbosity)
  -q, --quiet           quiet output (show errors only)
  -t, --test            disable Google spreadsheet update
"""
import argparse
import pyperclip

import gd2gs.logger as log

from gd2gs.config import Config
from gd2gs.bzilla import Bzilla
from gd2gs.jira import Jira
from gd2gs.gsheet import Gsheet
from gd2gs.source import SourceData

CONFIG_FILE = 'gd2gs.yaml'

# Debug messages:
SCRIPT_FINISHED = 'script finished'
SCRIPT_STARTED = 'script started'

# Warning messages:
NOT_AVAILABLE = ': data update from input is not available in Google sheet '

# Error messages:
UNKNOWN_SHEET = 'uknown sheet: '
UNKNOWN_SOURCE = 'unknown source'

def get_cli_parameters():
    """ Get parameters from CLI and check that they are correct """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, default=CONFIG_FILE,
            help='config file (default: '+CONFIG_FILE+')')
    parser.add_argument('-s', '--sheet', nargs='+', type=str, action='extend',
            help='use listed sheets')
    parser.add_argument('-v', '--verbose', action='count', dest='verbosity',
            default=0, help='verbose output (repeat for increased verbosity)')
    parser.add_argument('-q', '--quiet', action='store_const', const=-1,
            default=0, dest='verbosity', help='quiet output (show errors only)')
    parser.add_argument('-t', '--test', action="store_true",
            help='disable Google spreadsheet update')
    parser.add_argument('-a', '--add', action="store_true",
            help='enable to add missing items into the Google spreadsheet')
    args = parser.parse_args()
    log.setup(args.verbosity)
    return args.config, args.sheet, args.test, args.add

def get_sheets_and_data(source_access, config, selected_sheets):
    """ Get valid sheets list and source data """
    source_data = {}
    if not selected_sheets:
        selected_sheets = config.sheets
    else:
        for item in selected_sheets:
            if not item in config.sheets:
                log.error(UNKNOWN_SHEET + item)
    sheets_list = []
    for sheet_name, query in config.queries.items():
        if sheet_name in selected_sheets:
            source_data[sheet_name] = SourceData(source_access, query, config.sheet[sheet_name])
            sheets_list.append(sheet_name)
    return sheets_list, source_data

def update_row(s_sheet, s_key_index, g_sheet, g_row):
    """ Update the Google row with source data """
    for column in g_sheet.columns:
        if column in s_sheet.data.columns:
            g_sheet.loc[g_row, (column)] = \
                    s_sheet.data.loc[s_key_index, (column)]
        else:
            g_sheet.loc[g_row, (column)] = ""

def transform_data(source, google, sheet_conf, test_mode, enable_add):
    """ Copy transformed data from source to the target Google spreadsheet """
    key_google_dict = {}
    missing_all_google_key_values = []
    for sheet_name in google.active_sheets:
        key = sheet_conf[sheet_name].key
        key_google_dict[sheet_name] = {}
        for row in range(google.data[sheet_name].index.start, google.data[sheet_name].index.stop,
                google.data[sheet_name].index.step):
            key_google_dict[sheet_name][google.data[sheet_name][key][row]] = row

        for row in range(google.data[sheet_name].index.start, google.data[sheet_name].index.stop,
                google.data[sheet_name].index.step):
            key_value = str(google.data[sheet_name][key][row])
            if key_value in source[sheet_name].key_dict:
                key_index = source[sheet_name].key_dict[key_value]
                source[sheet_name].used_key[key_value] = True
            else:
                log.warning(key + ': ' + key_value + NOT_AVAILABLE + sheet_name)
                continue
            update_row(source[sheet_name], key_index, google.data[sheet_name], row)
        missing_google_keys = source[sheet_name].check_missing_keys(
                sheet_name, key, sheet_conf[sheet_name])
        missing_all_google_key_values = missing_all_google_key_values + missing_google_keys
        if enable_add and not test_mode:
            for key_value in missing_google_keys:
                log.info("missing row with the key " + key_value \
                        + " will be added into the sheet " + sheet_name)
                update_row(source[sheet_name], source[sheet_name].key_dict[key_value], \
                        google.data[sheet_name], len(google.data[sheet_name]))
    if missing_all_google_key_values:
        pyperclip.copy('\n'.join(map(str, missing_all_google_key_values)))

def main():
    """
    Get the config file, read source data and write them
    into the google spreadsheet.
    """
    log.debug(SCRIPT_STARTED)
    config_file_name, selected_sheets, test, add = get_cli_parameters()
    if test:
        log.info('test mode (Google spreadsheet update is disabled)')
    config = Config(config_file_name)
    if config.source == 'BUGZILLA':
        source_access = Bzilla(config.bugzilla_domain, config.bugzilla_url, config.bugzilla_api_key)
    elif config.source == 'JIRA':
        source_access = Jira(config.jira_server, config.jira_token, config.jira_max_results)
    else:
        log.error(UNKNOWN_SOURCE)
    log.check_error()    # if a source error occured, terminate the script
    sheets_list, data = get_sheets_and_data(source_access, config, selected_sheets)
    google_spreadsheet = Gsheet(config.spreadsheet_id, sheets_list, config.sheet)
    transform_data(data, google_spreadsheet, config.sheet, test, add)

    if not test:
        google_spreadsheet.update_spreadsheet()
        for sheet_name in sheets_list:
            for column in config.sheet[sheet_name].columns:
                if config.sheet[sheet_name].columns[column].link and \
                        config.sheet[sheet_name].key == column:
                    google_spreadsheet.update_column_with_links(sheet_name, column, \
                            config.sheet[sheet_name].columns[column].link)
    log.debug(SCRIPT_FINISHED)
