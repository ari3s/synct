""" Input spreadsheet class and operations """

import pathlib
import warnings

from json import loads

import pandas as pd

import gd2gs.logger as log

# Debug messages:
IDENTIFY_FILE_TYPE = 'identify input file type'
READ_INPUT_FILE = 'read data from the input file: '
SELECT_INPUT_FILE = 'select input data: '

# Error messages:
UNKNOWN_FILE_TYPE = 'unknown input file type'
READING_INPUT_FILE_FAILED = 'reading input file failed'

# Warning messages:
IGNORED_TABLE = 'table selection is ignored, not supported in CSV files'

# Spreadsheet engines per file name extension
engines = {'.csv': 'python', '.ods': 'odf', '.xls': 'xlrd', '.xlsx': 'openpyxl'}

class Xsheet:   # pylint: disable=too-few-public-methods
    """ Input spreadsheet file class """

    def __init__(self, config, file, table, offset):
        """
        Idetify data format of the the local file
        and read data that will be selected later on.
        """
        log.debug(IDENTIFY_FILE_TYPE)
        file_name = config.name if file is None else file
        try:
            engine = engines[pathlib.Path(file_name).suffix]
            log.debug(engine)
        except KeyError:
            log.fatal_error(UNKNOWN_FILE_TYPE)

        log.debug(READ_INPUT_FILE + file_name)
        table_name = config.table if table is None else table
        offset_value = config.offset if offset is None else offset
        try:
            # suppress warnig: Workbook contains no default style, apply openpyxl's default
            with warnings.catch_warnings(record=True):
                warnings.simplefilter('always')
                if pathlib.Path(file_name).suffix == '.csv':
                    if table_name:
                        log.warning(IGNORED_TABLE)
                    self.data = pd.read_csv(file_name, engine=engine,
                                            sep=None,   # python engine can detect the separator
                                            skiprows=offset_value, keep_default_na=False)
                elif table_name:
                    self.data = pd.read_excel(file_name, engine=engine, sheet_name=table_name,
                                              skiprows=offset_value, keep_default_na=False)
                else:
                    self.data = pd.read_excel(file_name, engine=engine,
                                              skiprows=offset_value, keep_default_na=False)
        except (OSError, ValueError) as exception:
            log.error(exception)
            log.error(READING_INPUT_FILE_FAILED)
            self.data = None
        for column in self.data:
            if  self.data[column].dtypes == 'datetime64[ns]':     # convert date to string
                self.data[column] = pd.to_datetime(self.data[column]).astype(str)

    def get_data(self, sheet_query):
        """ Query to input file """
        log.debug(SELECT_INPUT_FILE + str(sheet_query))
        try:
            data = loads(self.data.query(sheet_query).to_json(orient="records"))
        except Exception as exception:     # pylint: disable=broad-exception-caught
            log.error(exception)
            log.error(READING_INPUT_FILE_FAILED)
            data = None
        return data
