""" Input spreadsheet class and operations """

import pathlib
import warnings

from json import loads

import pandas as pd

import syncit.logger as log

# Debug messages:
IDENTIFY_INPUT_FILE_TYPE = 'identify input file type'
READ_INPUT_FILE = 'read data from the input file: '
INPUT_DATA_QUERY = 'input data query: '

# Error messages:
UNKNOWN_INPUT_FILE_TYPE = 'unknown input file type'
MISSING_OR_INCORRECT_INPUT_FILE = 'missing or incorrect input file'
READING_INPUT_FILE_FAILED = 'reading input file failed'
QUERY_FAILED = 'query failed in the configuration file for the sheet '
WRONG_OFFSET_INPUT_FILE = 'it could be a wrong offset of the header in the input file'

# Warning messages:
IGNORED_TABLE = 'table selection is ignored, not supported in CSV files'

# Input spreadsheet engines per file name extension
input_engines = {'.csv': 'python', '.ods': 'odf', '.xls': 'xlrd', '.xlsx': 'openpyxl'}

class Xsheet:   # pylint: disable=too-few-public-methods
    """ Input spreadsheet file class """

    def __init__(self, config, file, table, offset):
        """
        Idetify data format of the the local file
        and read data that will be selected later on.
        """
        log.debug(IDENTIFY_INPUT_FILE_TYPE)
        file_name = config.name if file is None else file
        try:
            engine = input_engines[pathlib.Path(file_name).suffix]
            log.debug(engine)
        except KeyError:
            log.fatal_error(UNKNOWN_INPUT_FILE_TYPE)
        except TypeError:
            log.fatal_error(MISSING_OR_INCORRECT_INPUT_FILE)

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
            log.fatal_error(READING_INPUT_FILE_FAILED)
        for column in self.data:
            if  self.data[column].dtypes == 'datetime64[ns]':     # convert date to string
                self.data[column] = pd.to_datetime(self.data[column]).astype(str)

    def data_query(self, sheet, sheet_query):
        """ Query to input file """
        log.debug(INPUT_DATA_QUERY + str(sheet_query))
        try:
            data = loads(self.data.query(sheet_query).to_json(orient="records"))
        except (SyntaxError, ValueError) as exception:
            log.error(QUERY_FAILED + sheet + ':\n' + sheet_query)
            log.fatal_error(exception)
        except (pd.errors.UndefinedVariableError) as exception:
            log.error(QUERY_FAILED + sheet + ':\n' + sheet_query)
            log.error(WRONG_OFFSET_INPUT_FILE)
            log.fatal_error(exception)
        return data
