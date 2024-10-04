"""
Testing the synct script functionality that covers
adding rows and default columns with source data
simulating Jira data structure.
"""

# Disable pylint message regarding similar lines in 2 files
# pylint: disable=R0801

import json

from dataclasses import dataclass
from pathlib import Path

import unittest
from unittest.mock import patch
from parameterized import parameterized

import pandas as pd
from pandas.testing import assert_frame_equal

import yaml

from synct.config import Column, Sheet
from synct.source import SourceData
from synct.synct import transform_data

TESTS_DIR = Path(__file__).parent
DATA_DIR = TESTS_DIR / 'data'
SUFFIX = '.txt'

CONFIG_DATA = DATA_DIR / 'config_jira.yaml'
SOURCE_DATA = DATA_DIR / 'source_data_jira.json'
INITIAL_DATA = DATA_DIR / 'initial_data_jira.txt'

EXPECTED_DATA_0 = DATA_DIR / 'expected_data_jira_0.txt'
EXPECTED_DATA_1 = DATA_DIR / 'expected_data_jira_1.txt'
EXPECTED_DATA_2 = DATA_DIR / 'expected_data_jira_2.txt'
EXPECTED_DATA_3 = DATA_DIR / 'expected_data_jira_3.txt'

SHEET = 'TEST'

@dataclass
class Args:
    """ Default command line arguments of the script """
    add = False
    remove = False
    noupdate = False

class JiraObject:               # pylint: disable=too-few-public-methods
    """ Object simulating Jira data """

def allow_duplicated_columns(df):
    """ Transformation data structure like obtained from pd.read_excel """
    col_map = []
    for col in df.columns:
        if col.rpartition('.')[0]:
            col_name = col.rpartition('.')[0]
            in_map = col.rpartition('.')[0] in col_map
            last_is_num = col.rpartition('.')[-1].isdigit()
            dupe_count = col_map.count(col_name)
            if in_map and last_is_num and (int(col.rpartition('.')[-1]) == dupe_count):
                col_map.append(col_name)
                continue
        col_map.append(col)
    df.columns = col_map

def dictionary_to_object(data):
    """ Trasnform dictionary to object """
    if isinstance(data, list):
        data = [dictionary_to_object(item) for item in data]
    if not isinstance(data, dict):
        return data
    jira_object = JiraObject()
    for item in data:
        jira_object.__dict__[item] = dictionary_to_object(data[item])
    return jira_object

def operation(jira_mode, initial_data, mock_tsheet_class, \
        add, default_columns, inherit_formulas):        # pylint: disable=too-many-arguments
    """ Make the operation with data and return the final data """

    # Arguments set-up
    args = Args()
    args.add = add

    # Prepare the mock Gsheet instance
    target_spreadsheet_data = pd.read_fwf(initial_data, encoding='utf-8', dtype=str)
    allow_duplicated_columns(target_spreadsheet_data)
    tsheet_instance = mock_tsheet_class.return_value
    tsheet_instance.active_sheets = [SHEET]
    tsheet_instance.data = {SHEET: target_spreadsheet_data}
    tsheet_instance.unique_columns = \
            {SHEET: list(dict.fromkeys(target_spreadsheet_data.columns.values.tolist()))}

    # Read source data
    with open(SOURCE_DATA, encoding='utf-8') as json_file:
        source_data = json.load(json_file)

    # Configure tests parameters
    sheet_conf = configure(default_columns, inherit_formulas)
    tsheet_instance.sheets_config = sheet_conf

    # Set up source data instance
    if jira_mode:
        # Transform dictionary to object
        source_data_object = dictionary_to_object(source_data)
        source_data_instance = set_source_data_instance( \
                source_data_object, sheet_conf, tsheet_instance)
    else:
        # Keep dictionary source format
        source_data_instance = set_source_data_instance(source_data, sheet_conf, tsheet_instance)

    # Call the function under test
    transform_data(source_data_instance, tsheet_instance, args)

    return tsheet_instance.data[SHEET]

def configure(default_columns, inherit_formulas):
    """ Configure test parameters """
    header_offset = 0
    delimiter = ' '
    sheet_columns = {}
    key = 'Issue_key'

    with open(CONFIG_DATA, encoding='utf-8') as config_file:
        config_sheet_columns = yaml.safe_load(config_file.read())

    sheet_conf = {}
    sheet_conf[SHEET] = Sheet(header_offset, delimiter, default_columns, \
                              inherit_formulas, sheet_columns, key)
    for column in config_sheet_columns:
        sheet_conf[SHEET].columns[column] = Column()
        sheet_conf[SHEET].columns[column].data = config_sheet_columns[column]
    return sheet_conf

def set_source_data_instance(source_data, sheet_conf, tsheet_instance):
    """ Set up source data instance """
    source_data_instance = {}
    if sheet_conf[SHEET].default_columns:
        source_data_instance[SHEET] = SourceData(source_data, \
            sheet_conf[SHEET], SHEET, tsheet_instance.data[SHEET])
    else:
        source_data_instance[SHEET] = SourceData(source_data, \
            sheet_conf[SHEET])
    return source_data_instance

def custom_name_func(testcase_func, param_num, param):
    """
    The names of the test cases generated by @parameterized.expand
    :param testcase_func: will be the function to be tested
    :param param_num: will be the index of the test case parameters in the list of parameters
    :param param: (an instance of param) will be the parameters which will be used.
    :return: test case name
    """
    return (f'{testcase_func.__name__}_'
            f'{parameterized.to_safe_name("_".join([str(param.args[0]), param_num]))}')

class TestTransformDataGeneral(unittest.TestCase):
    """ Test the synct script functionality with dictionary format source data """
    @parameterized.expand([
        # Order of parameters:
        # test name, add rows, default columns, inherit formulas, expected data
        ('disabledparameters', False, False, False, EXPECTED_DATA_0),
        ('addrows', True, False, False, EXPECTED_DATA_1),
        ('defaultcolumns', False, True, False, EXPECTED_DATA_2),
        ('addrows_defaultcolumns', True, True, False, EXPECTED_DATA_3)
    ], name_func=custom_name_func)

    @patch('synct.tsheet.Tsheet', autospec=True)
    def test_transform_data(self, _, add, default_columns, inherit_formulas, expected_data, \
            mock_tsheet_class):           # pylint: disable=too-many-arguments
        """ Testing with fake data """
        transformed_data = operation(False, INITIAL_DATA, mock_tsheet_class, add, default_columns, \
                inherit_formulas).fillna('')
        expected_data = pd.read_fwf(expected_data, encoding='utf-8', dtype=str).fillna('')
        allow_duplicated_columns(expected_data)
        assert_frame_equal(transformed_data, expected_data, check_dtype=False)

class TestTransformDataJira(unittest.TestCase):
    """ Test the synct script functionality with object format source data """
    @parameterized.expand([
        # Order of parameters:
        # test name, add rows, default columns, inherit formulas, expected data
        ('disabledparameters', False, False, False, EXPECTED_DATA_0),
        ('addrows', True, False, False, EXPECTED_DATA_1),
        ('defaultcolumns', False, True, False, EXPECTED_DATA_2),
        ('addrows_defaultcolumns', True, True, False, EXPECTED_DATA_3)
    ], name_func=custom_name_func)

    @patch('synct.tsheet.Tsheet', autospec=True)
    def test_transform_data(self, _, add, default_columns, inherit_formulas, expected_data, \
            mock_tsheet_class):           # pylint: disable=too-many-arguments
        """ Testing with fake data """
        transformed_data = operation(True, INITIAL_DATA, mock_tsheet_class, add, default_columns, \
                inherit_formulas).fillna('')
        expected_data = pd.read_fwf(expected_data, encoding='utf-8', dtype=str).fillna('')
        allow_duplicated_columns(expected_data)
        assert_frame_equal(transformed_data, expected_data, check_dtype=False)
