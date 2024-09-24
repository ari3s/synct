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

synct.config: Config access and operations
"""

from dataclasses import dataclass

import pathlib
import yaml

import synct.logger as log

from synct.bzilla import Bzilla
from synct.git import Github, Gitlab
from synct.jira import Jira
from synct.xsheet import Xsheet

BUGZILLA = 'BUGZILLA'
API_KEY = 'API_KEY'
DOMAIN = 'DOMAIN'
URL = 'URL'

GITHUB = 'GITHUB'
GITLAB = 'GITLAB'
SEARCH_API = 'SEARCH_API'
TOKEN = 'TOKEN'

JIRA = 'JIRA'
SERVER = 'SERVER'

FILE = 'FILE'
TYPE = 'TYPE'
SPREADSHEET = 'SPREADSHEET'
FILE_NAME = 'FILE_NAME'
OFFSET = 'OFFSET'
TABLE = 'TABLE'

MAX_RESULTS = 'MAX_RESULTS'
DEFAULT_MAX_RESULTS = 100
QUERY = 'QUERY'

SPREADSHEET_ID = 'SPREADSHEET_ID'
SHEETS = 'SHEETS'
NAME = 'NAME'

HEADER_OFFSET = 'HEADER_OFFSET'
DEFAULT_HEADER_OFFSET = 0
DEFAULT_COLUMNS = 'DEFAULT_COLUMNS'
INIT_DEFAULT_COLUMNS = False
INHERIT_FORMULAS = 'INHERIT_FORMULAS'
INIT_INHERIT_FORMULAS = False
SHEET_COLUMNS = 'SHEET_COLUMNS'
SOURCE = 'SOURCE'
FROM = 'FROM'
GET = 'GET'
CONDITION = 'CONDITION'
KEY = 'KEY'
LINK = 'LINK'
OPTIONAL = 'OPTIONAL'
DELIMITER = 'DELIMITER'
DEFAULT_DELIMITER = ' '

# Debug messages:
READ_CONFIG_FILE = 'read config file'
SHEET = 'sheet'
SPREADSHEET_ = 'spreadsheet: '

# Warning messages - command line arguments:
UNKNOWN_SHEET = 'uknown sheet: '

# Error messages - config file:
CONFIG_FILE = 'configuration file: '
CONFIG_FILE_EXTENSION_IS_NOT_YAML = ': extension in not .yaml'
CONFIG_FILE_MISSING_INPUT = 'input is missing in the config file'

# Error messages - Bugzilla:
CONFIG_FILE_MISSING_BUGZILLA_API_KEY_FILE = 'Bugzilla API key file is not set in the config file'
CONFIG_FILE_MISSING_BUGZILLA_DOMAIN = 'Bugzilla domain is not set in the config file'
CONFIG_FILE_MISSING_BUGZILLA_URL = 'Bugzilla URL is not set in the config file'

# Error messages - GitHub:
CONFIG_FILE_MISSING_GITHUB_URL = 'GitHub search API URL is not set in the config file'

# Error messages - GitLab:
CONFIG_FILE_MISSING_GITLAB_TOKEN = 'GitLab access token is not set in the config file'
CONFIG_FILE_MISSING_GITLAB_URL = 'GitLab search API URL is not set in the config file'

# Error messages - Jira:
CONFIG_FILE_MISSING_JIRA_TOKEN = 'Jira access token is not set in the config file'
CONFIG_FILE_MISSING_JIRA_URL = 'Jira server url is not set in the config file'

# Error messages - file:
CONFIG_FILE_MISSING_FILE_TYPE = 'missing type of the input file'
CONFIG_FILE_WRONG_FILE_TYPE = 'wrong type of the input file'

# Error messages - target spreadsheet:
CONFIG_FILE_MISSING_KEY = 'missing key in the config file'
CONFIG_FILE_MISSING_QUERY = 'query is not set in the config file for the sheet '
CONFIG_FILE_MISSING_SHEET = 'no sheet is set in the config file'
CONFIG_FILE_MISSING_SPREADSHEET = 'target spreadsheet is not set in the config file'
CONFIG_FILE_MORE_KEYS = 'more than one key is set in the config file'
CONFIG_FILE_WRONG_SPREADSHEET = 'spreadsheet_id must be a string in the config file'

@dataclass
class Sheet:
    """ Sheet data class """
    header_offset: int = DEFAULT_HEADER_OFFSET
    delimiter: str = DEFAULT_DELIMITER
    default_columns: bool = INIT_DEFAULT_COLUMNS
    inherit_formulas: bool = INIT_INHERIT_FORMULAS
    columns: dict = None
    key: str = None

@dataclass
class Column:
    """ Column data class """
    data: str = None
    gets: dict = None
    condition: dict = None
    optional: str = None
    link: str = None
    delimiter: str = DEFAULT_DELIMITER
    inherit_formulas: bool = INIT_INHERIT_FORMULAS

class Config:   # pylint: disable=too-many-instance-attributes
    """ Config parameters """

    def __init__(self, args):
        """ Get config data from the config file """
        log.debug(READ_CONFIG_FILE)
        if pathlib.Path(args.config).suffix != '.yaml':
            log.warning(CONFIG_FILE + args.config + CONFIG_FILE_EXTENSION_IS_NOT_YAML)
        try:
            with open(args.config, encoding='utf-8') as config_file:
                config_data = yaml.safe_load(config_file)
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exception:
            log.error(CONFIG_FILE + args.config)
            log.fatal_error(exception)
        self.source = get_source(config_data, args)
        self.config_tsheet_type(config_data)
        self.config_tsheet(config_data, args)
        log.check_error()

    def config_tsheet(self, config_data, args):
        """ Configure target spreadsheet params """
        spreadsheet = get_sheet_config(config_data, None)
        log.debug(SPREADSHEET_ + str(spreadsheet))
        if SHEETS in config_data:
            self.sheets = {}
            self.queries = {}
            sheets_list = []
            for sheet_item in config_data[SHEETS]:
                name = sheet_item[NAME]
                sheets_list.append(name)
                if args.sheet and name not in args.sheet:
                    continue
                query = get_config(sheet_item, QUERY, CONFIG_FILE_MISSING_QUERY + sheet_item[NAME])
                self.queries[name] = query
                self.sheets[name] = get_sheet_config(sheet_item, spreadsheet)
                log.debug(SHEET + ' ' + name + ': ' + str(self.sheets[name]))
                if not self.sheets[name].key:
                    log.error(CONFIG_FILE_MISSING_KEY + ' (' + SHEET + ': ' + name + ')')
        else:
            log.error(CONFIG_FILE_MISSING_SHEET)
        # Validate sheets on the command line
        if args.sheet:
            for item in args.sheet:
                if item not in sheets_list:
                    log.warning(UNKNOWN_SHEET + item)

    def config_tsheet_type(self, config_data):
        """ Configure target spreadsheet type """
        if SPREADSHEET in config_data:
            self.module = 'synct.ysheet'
            self.target = 'Ysheet'
            self.spreadsheet = get_config(config_data, SPREADSHEET,
                                             CONFIG_FILE_MISSING_SPREADSHEET)
        else:
            self.module = 'synct.gsheet'
            self.target = 'Gsheet'
            self.spreadsheet_id = get_config(config_data, SPREADSHEET_ID,
                                             CONFIG_FILE_MISSING_SPREADSHEET)
            if not isinstance(self.spreadsheet_id, str):
                log.fatal_error(CONFIG_FILE_WRONG_SPREADSHEET)

def get_source(config_data, args):
    """ Get input presented in the config file """
    param = None
    source = None
    if BUGZILLA in config_data:
        param = BUGZILLA
        source = access_bugzilla(config_data)
    elif GITHUB in config_data:
        param = GITHUB
        source = access_github(config_data)
    elif GITLAB in config_data:
        param = GITLAB
        source = access_gitlab(config_data)
    elif JIRA in config_data:
        param = JIRA
        source = access_jira(config_data)
    elif FILE in config_data:
        param = FILE
        source = access_xsheet(config_data, args)
    else:
        log.error(CONFIG_FILE_MISSING_INPUT)
    try:
        value_str = str(config_data[param])
    except KeyError:
        log.check_error()
    log.debug(param + ': ' + value_str)
    return source

def access_bugzilla(config_data):
    """ Set up Bugzilla access """
    bugzilla_domain = get_config(config_data[BUGZILLA], DOMAIN, \
            CONFIG_FILE_MISSING_BUGZILLA_DOMAIN)
    bugzilla_url = get_config(config_data[BUGZILLA], URL, \
            CONFIG_FILE_MISSING_BUGZILLA_URL)
    bugzilla_api_key = get_config(config_data[BUGZILLA], API_KEY, \
            CONFIG_FILE_MISSING_BUGZILLA_API_KEY_FILE)
    return Bzilla(bugzilla_domain, bugzilla_url, bugzilla_api_key)

def access_github(config_data):
    """ Set up GitHub access """
    github_url = get_config(config_data[GITHUB], SEARCH_API, CONFIG_FILE_MISSING_GITHUB_URL)
    github_token = get_config_with_default(config_data[GITHUB], TOKEN, None)
    return Github(github_url, github_token)

def access_gitlab(config_data):
    """ Set up GitLab access """
    gitlab_url = get_config(config_data[GITLAB], SEARCH_API, CONFIG_FILE_MISSING_GITLAB_URL)
    gitlab_token = get_config(config_data[GITLAB], TOKEN, CONFIG_FILE_MISSING_GITLAB_TOKEN)
    return Gitlab(gitlab_url, gitlab_token)

def access_jira(config_data):
    """ Set up Jira access """
    jira_server = get_config(config_data[JIRA], SERVER, CONFIG_FILE_MISSING_JIRA_URL)
    jira_token = get_config(config_data[JIRA], TOKEN, CONFIG_FILE_MISSING_JIRA_TOKEN)
    jira_max_results = int(get_config_with_default(config_data[JIRA], \
            MAX_RESULTS, DEFAULT_MAX_RESULTS))
    return Jira(jira_server, jira_token, jira_max_results)

def access_xsheet(config_data, args):
    """ Set up input file access and parameters """
    if get_config(config_data[FILE], TYPE, CONFIG_FILE_MISSING_FILE_TYPE) != SPREADSHEET:
        log.fatal_error(CONFIG_FILE_WRONG_FILE_TYPE)
    name = get_config_with_default(config_data[FILE], FILE_NAME, None)
    table = get_config_with_default(config_data[FILE], TABLE, None)
    offset = get_config_with_default(config_data[FILE], OFFSET, DEFAULT_HEADER_OFFSET)
    return Xsheet(args, name, table, offset)

def get_sheet_config(config_data, spreadsheet):
    """ Get target sheet params """
    key = None
    columns = {}
    if spreadsheet:
        header_offset = spreadsheet.header_offset
        delimiter = spreadsheet.delimiter
        default_columns = spreadsheet.default_columns
        inherit_formulas = spreadsheet.inherit_formulas
        key = spreadsheet.key
        for column in spreadsheet.columns:
            columns[column] = spreadsheet.columns[column]
    else:    # global parameters
        header_offset = DEFAULT_HEADER_OFFSET
        delimiter = DEFAULT_DELIMITER
        default_columns = INIT_DEFAULT_COLUMNS
        inherit_formulas = INIT_INHERIT_FORMULAS
    if HEADER_OFFSET in config_data:
        header_offset = int(config_data[HEADER_OFFSET])
    if DELIMITER in config_data:
        delimiter = config_data[DELIMITER]
        for column in columns:          # pylint: disable=consider-using-dict-items
            columns[column].delimiter = delimiter
    if DEFAULT_COLUMNS in config_data:
        default_columns = config_data[DEFAULT_COLUMNS]
    if INHERIT_FORMULAS in config_data:
        inherit_formulas = config_data[INHERIT_FORMULAS]
        for column in columns:          # pylint: disable=consider-using-dict-items
            columns[column].inherit_formulas = inherit_formulas
    if SHEET_COLUMNS in config_data:
        for column, data in config_data[SHEET_COLUMNS].items():
            columns[column] = Column()
            columns[column].delimiter = get_column_param(data, DELIMITER, delimiter)
            columns[column].inherit_formulas = get_column_param( \
                    data, INHERIT_FORMULAS, inherit_formulas)
            key = get_column_config(key, column, columns[column], data)
    if spreadsheet and not columns:
        delimiter = spreadsheet.delimiter
        inherit_formulas = spreadsheet.inherit_formulas
        columns = spreadsheet.columns
        key = spreadsheet.key
    return Sheet(header_offset, delimiter, default_columns, inherit_formulas, columns, key)

def get_column_param(c_data, param, default):
    """ Get column parameter that can have also a default value """
    return c_data[param] if param in c_data else default

def get_column_config(key, column, col, c_data):
    """ Get column configuration """
    if isinstance(c_data, dict):
        if KEY in c_data:
            if key:
                log.error(CONFIG_FILE_MORE_KEYS)
            key = column
        if LINK in c_data:
            col.link = c_data[LINK]
        if OPTIONAL in c_data:
            col.optional = c_data[OPTIONAL]
        if SOURCE in c_data:
            get_source_config(col, c_data)
        else:
            col.data = column
    else:
        col.data = c_data
    return key

def get_source_config(col, c_data):
    """ Get configuration of source data handling """
    col.delimiter2 = get_column_param(c_data[SOURCE], DELIMITER, col.delimiter)
    if isinstance(c_data[SOURCE], dict):
        if FROM in c_data[SOURCE]:
            col.data = c_data[SOURCE][FROM]
        if GET in c_data[SOURCE]:
            col.gets = c_data[SOURCE][GET]
        if CONDITION in c_data[SOURCE]:
            col.condition = c_data[SOURCE][CONDITION]
        if LINK in c_data[SOURCE]:
            col.link = c_data[SOURCE][LINK]
        if OPTIONAL in c_data[SOURCE]:
            col.optional = c_data[SOURCE][OPTIONAL]
        if INHERIT_FORMULAS in c_data[SOURCE]:
            col.inherit_formulas = c_data[SOURCE][INHERIT_FORMULAS]
    else:
        col.data = c_data[SOURCE]

def get_config(config_data, param, error_message):
    """ Get param presented in the config file """
    if param not in config_data:
        log.error(error_message)
    try:
        value_str = str(config_data[param])
    except KeyError:
        log.check_error()
    log.debug(param + ': ' + value_str)
    return config_data[param]

def get_config_with_default(config_data, param, default_value):
    """ Get param from the config file. If not present, setup default value. """
    if param in config_data:
        value = config_data[param]
        default_info = ''
    else:
        value = default_value
        default_info = ' (default value)'
    log.debug(param + ': ' + str(value) + default_info)
    return value
