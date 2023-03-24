""" Source data class and operations """
import builtins
import re

import pandas as pd
import gd2gs.logger as log

MISSING_IN_THE_SPREADSHEET = 'missing in Google sheet'

class SourceData:   # pylint: disable=too-few-public-methods
    """ Source data class """
    data = {}
    key_dict = {}
    used_key = {}

    def __init__(self, source, query, sheet_config):
        """ Read source data """
        self.key_dict = {}
        self.used_key = {}
        source_data = source.get_data(query)
        converted_data = []
        columns_list = list(sheet_config.columns.keys())
        index = 0
        for source_item in source_data:   #pylint: disable=unused-variable
            raw = {}
            for value in columns_list:
                raw[value] = ''
            for column in sheet_config.columns:
                try:
                    value = eval('source_item.' + sheet_config.columns[column].data)
                except:
                    continue
                if value is None:
                    continue
                if not isinstance(value, str):
                    try:
                        iter(value)
                    except TypeError:
                        pass
                raw[column] = evaluate(value, sheet_config.columns[column], source_item, \
                        column == sheet_config.key)
            key_value = raw[sheet_config.key]
            self.key_dict[key_value] = index
            index = index + 1
            self.used_key[key_value] = False
            converted_data.append(list(raw.values()))
        self.data = pd.DataFrame(converted_data[0:], index=range(0, len(converted_data)), \
                                 columns=columns_list)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def check_missing_keys(self, sheet, key):
        """ Check missing keys in source data """
        missing_keys = []
        for key_value, used in self.used_key.items():
            if not used:
                missing_keys.append(key_value)
                message = key + ': ' + key_value + ': ' + MISSING_IN_THE_SPREADSHEET + ' ' + sheet
                log.warning(message)
        return missing_keys

def trans_value(config, conf_item_list, source_item):  #pylint: disable=unused-argument
    """ Get and transform value from Jira to fit with other formats """
    value = []
    for key in conf_item_list:
        try:
            d_value = eval('source_item.' + config.data + '.' + key)
        except:
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

def handle_gets(value, config, source_item):
    """ Handle gets """
    tmp = []
    for conf_item in config.gets:
        conf_item_list = list(conf_item.keys())
        if type(value).__name__ not in dir(builtins):  # jira.resources.PropertyHolder object
            value = trans_value(config, conf_item_list, source_item)
        for s_data in value:
            if config.condition:
                if not is_subset(s_data, config.condition):
                    continue
            tmp_value = ''
            flag = False
            for key in conf_item_list:
                if key in s_data:
                    if re.match(conf_item[key], s_data[key]):
                        if flag:
                            tmp_value = tmp_value + config.delimiter2
                        tmp_value = tmp_value + s_data[key]
                        flag = True
                    else:
                        flag = False
                        break
            if flag:
                tmp.append(tmp_value)
    return tmp

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
    elif isinstance(value, str):
        if link:
            proper_value = link + value
        else:
            proper_value = value
    else:
        if link:
            proper_value = link + str(value)
        else:
            proper_value = str(value)
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
