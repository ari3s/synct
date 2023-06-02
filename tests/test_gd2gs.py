""" Testing """
from pathlib import Path
from flexmock import flexmock

import pandas as pd
from pandas.testing import assert_frame_equal

from gd2gs.config import Column, Sheet
from gd2gs.source import SourceData
from gd2gs.gsheet import Gsheet
from gd2gs.gd2gs import transform_data

TESTS_DIR = Path(__file__).parent
DATA_DIR = TESTS_DIR / "data"

TEST_JIRA_DATA = DATA_DIR / "test_jira_data.txt"
TEST_SOURCE_GOOGLE_DATA = DATA_DIR / "test_source_google_data.txt"
TEST_TARGET_GOOGLE_DATA = DATA_DIR / "test_target_google_data.txt"

class Args:
    """ Arguments """
    add = None
    remove = None
    test = None

class TestWdsClass:    # pylint: disable=too-few-public-methods
    """ Testing class """

    def test_data(self):
        """ Function testing with fake data from Excel spreadsheet """
        args = Args()
        key = "ISSUE"

        jira = {}

        jira_data = pd.read_table(TEST_JIRA_DATA)
        parsed = jira_data.to_dict()

        flexmock(SourceData, data = jira_data, key_dict = {},
                 used_key = {}, __init__ = None)
        jira['TEST'] = SourceData('', '', '')
        for item in parsed[key]:
            jira['TEST'].key_dict[parsed[key][item]] = item
            jira['TEST'].used_key[parsed[key][item]] = False

        data_spreadsheet = {}
        data_spreadsheet["TEST"] = pd.read_fwf(TEST_SOURCE_GOOGLE_DATA)
        flexmock(Gsheet, active_sheets = ["TEST"], data = data_spreadsheet,\
                 __init__ = None)
        google = Gsheet('', '', '')

        sheet_conf = {}
        sheet_conf["TEST"] = Sheet(0, {}, {}, key)
        for column in jira_data:
            sheet_conf["TEST"].columns[column] = Column

        transform_data(jira, google, sheet_conf, args)
        assert_frame_equal(google.data["TEST"],
                           pd.read_fwf(TEST_TARGET_GOOGLE_DATA), check_dtype=False)
