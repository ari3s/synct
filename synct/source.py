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


synct.source: Source data operations
"""

import builtins
import re

from pprint import pformat

import pandas as pd
import synct.logger as log

SOURCE_DATA_KEY = 'SOURCE DATA: key = '

# Warning messages:
DUPLICATED_TARGET_COLUMN_NAME = 'duplicated column name in the target sheet '
MISSING_IN_THE_TARGET_SPREADSHEET = 'missing in the target spreadsheet'

class SourceData:
    """ Source data class """
    data = {}
    key_dict = {}
    used_key = {}

    def __init__(self, source_data, sheet_config, target_sheet_name=None, target_sheet=None):
        """ Convert source data """
        self.key_dict = {}
        self.used_key = {}
        converted_data = []
        columns_list = create_columns_list(sheet_config, target_sheet_name, target_sheet)
        index = 0
        for source_item in source_data:
            key_value = get_value(source_item, sheet_config, sheet_config.key)
            if key_value is None:
                continue
            if not isinstance(key_value, str):
                try:
                    key_value = str(key_value)
                    if key_value == '':
                        continue
                except TypeError:
                    continue
            display_source_record(source_item, key_value, index)
            row = get_columns(source_item, sheet_config, target_sheet, key_value, columns_list)
            self.key_dict[key_value] = index
            index = index + 1
            self.used_key[key_value] = False
            converted_data.append(list(row.values()))
        self.data = pd.DataFrame(converted_data[0:], index=range(0, len(converted_data)), \
                                 columns=columns_list)

    def check_missing_keys(self, sheet, key, sheet_config, enable_add):
        """ Check missing keys in source data """
        missing_keys = []
        for key_value, used in self.used_key.items():
            if not used:
                if self.found_key(sheet_config, key_value):
                    continue
                missing_keys.append(str(key_value))
                message = key + ': ' + str(key_value) + ': ' + \
                        MISSING_IN_THE_TARGET_SPREADSHEET + ' ' + sheet
                if enable_add:
                    log.info(message)
                else:
                    log.warning(message)
        return missing_keys

    def found_key(self, sheet_config, key_value):
        """ Return the key is (not) found """
        key_index = self.key_dict[key_value]
        found = False
        for column in self.data.columns:
            try:
                option = sheet_config.columns[column].optional
                if option:
                    if re.match(option, self.data.loc[key_index, (column)]):
                        found = True
                        break
            except KeyError:        # not configured default column
                continue
        return found

def cell_init_value(target_sheet, column, sheet_config, key_value):
    """ Set an initial value of the cell """
    value = ''
    if target_sheet is not None and column in target_sheet.columns:
        target_row = None
        # Find a row with the key
        for row in target_sheet.index:
            if str(target_sheet.loc[row, (sheet_config.key)]) == str(key_value):
                target_row = row
                break
        if target_row is not None:         # original value in the default column
            value = target_sheet.loc[target_row, (column)]
    return value

def create_columns_list(sheet_config, target_sheet_name, target_sheet):
    """ Create a columns list """
    columns_list = list(sheet_config.columns.keys())
    if target_sheet is not None:
        duplicates = []
        for column in target_sheet.columns:
            if column in duplicates:
                col = column if column else "<empty string>"
                log.warning(DUPLICATED_TARGET_COLUMN_NAME + target_sheet_name + ': ' +col)
            duplicates.append(column)
            if column not in columns_list:
                columns_list.append(column)
    return columns_list

def display_source_record(source_item, key_value, index):
    """ Display the first source data structured record in the debug mode """
    if index > 0 or not log.debug_level():
        return
    if isinstance(source_item, (float, int, str, list, dict, tuple, set)):
        sd_string = pformat(source_item)
    else:
        for attr in dir(source_item):
            if attr == '__dict__':
                sd_string = pformat(getattr(source_item, attr))
    log.debug(SOURCE_DATA_KEY + key_value + '\n' + sd_string)

def get_columns(source_item, sheet_config, target_sheet, key_value, columns_list):
    """ Get column values in the row """
    row = {}
    for column in columns_list:
        row[column] = cell_init_value(target_sheet, column, sheet_config, key_value)
        config_column = column in sheet_config.columns
        value = get_value(source_item, sheet_config, column)
        if value is None:
            continue
        if not isinstance(value, str):
            try:
                iter(value)
            except TypeError:
                pass
        if config_column:
            row[column] = evaluate(value, sheet_config.columns[column], source_item, \
                    column == sheet_config.key)
        elif isinstance(value, list):
            row[column] = sheet_config.delimiter.join(map(str, value))
        else:
            row[column] = str(value)
    return row

def get_value(source_item, sheet_config, column):
    """ Get value from source """
    try:
        value = source_item[sheet_config.columns[column].data]
    except (KeyError, TypeError):
        try:
            value = source_item[column]
        except (KeyError, TypeError):
            try:
                value = eval('source_item.' + sheet_config.columns[column].data)    #pylint: disable=eval-used
            except KeyError:
                try:
                    value = eval('source_item.' + column)    #pylint: disable=eval-used
                except (AttributeError, SyntaxError):
                    return None
            except (AttributeError, SyntaxError, TypeError):
                return None
    return value

def trans_value(config, conf_item_keys_list, source_item):  #pylint: disable=unused-argument
    """ Get and transform value from Jira to fit with other formats """
    value = []
    for key in conf_item_keys_list:
        try:
            d_value = eval('source_item.' + config.data + '.' + key)    #pylint: disable=eval-used
        except TypeError:
            continue
        if isinstance(d_value, list):
            for item in d_value:
                e_value = {}
                e_value[key] = item
                value.append(e_value)
        else:
            e_value = {}
            e_value[key] = d_value
            value.append(e_value)
    return value

def parse_gets(gets, config, conf_item_keys_list, conf_item, s_data):
    """ Parse gets """
    gets_item = ''
    flag = False
    for key in conf_item_keys_list:
        if key in s_data:
            if re.match(conf_item[key], s_data[key]):
                if flag:
                    gets_item = gets_item + config.delimiter2
                gets_item = gets_item + s_data[key]
                flag = True
            else:
                flag = False
                break
    if flag:
        gets.append(gets_item)
    return gets

def handle_gets(value, config, source_item):
    """ Handle gets """
    gets = []
    for conf_item in config.gets:
        conf_item_keys_list = list(conf_item.keys())
        if type(value).__name__ not in dir(builtins):  # jira.resources.PropertyHolder object
            value = trans_value(config, conf_item_keys_list, source_item)
        for s_data in value:
            if config.condition and not is_subset(s_data, config.condition):
                continue
            gets = parse_gets(gets, config, conf_item_keys_list, conf_item, s_data)
    return gets

def evaluate(value, config, source_item, column_is_key):
    """ Evaluate getting values and return a proper string """
    proper_value = ''
    link = None
    if config.link and not column_is_key:
        link = config.link
    if config.gets:
        value = handle_gets(value, config, source_item)
    if isinstance(value, list):
        if link:
            for index, element in enumerate(value):
                value[index] = link + element
        proper_value = config.delimiter.join(map(str, value))
    else:
        proper_value = link + str(value) if link else str(value)
    return proper_value

def check_eq(main_dict, sub_dict):
    """ Check nested directories """
    if not isinstance(main_dict, (dict, list)):
        return main_dict == sub_dict
    if isinstance(main_dict, list):
        # check for nesting dictionaries in list
        return all(check_eq(x, y) for x, y in zip(main_dict, sub_dict))
    # check for all keys
    return all(main_dict.get(index) == sub_dict[index] or check_eq(main_dict.get(index), \
            sub_dict[index]) for index in sub_dict)

def is_subset(main_dict, sub_dict):
    """ Check if nested directory is inlcuded in other one """
    if isinstance(main_dict, list):
        # any matching dictionary in list
        return any(is_subset(index, sub_dict) for index in main_dict)
    # any matching nested dictionary
    return check_eq(main_dict, sub_dict) or (isinstance(main_dict, dict) and any( \
            is_subset(y, sub_dict) for y in main_dict.values()))
