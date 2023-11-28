""" Input spreadsheet class and operations """

import pathlib
import warnings

from json import loads

import pandas as pd

import synct.logger as log

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

class Xsheet:
    """ Input spreadsheet file class """

    def __init__(self, args, name, table, offset):
        """
        Idetify data format of the the local file
        and read data that will be selected later on.
        """
        self.get_input(args, name)
        self.read_input_file(args, table, offset)
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

    def get_input(self, args, name):
        """ Indetify input file type """
        log.debug(IDENTIFY_INPUT_FILE_TYPE)
        self.file_name = name if args.file is None else args.file
        try:
            self.engine = input_engines[pathlib.Path(self.file_name).suffix]
            log.debug(self.engine)
        except KeyError:
            log.fatal_error(UNKNOWN_INPUT_FILE_TYPE)
        except TypeError:
            log.fatal_error(MISSING_OR_INCORRECT_INPUT_FILE)

    def read_input_file(self, args, table, offset):
        """ Read input file """
        log.debug(READ_INPUT_FILE + self.file_name)
        table_name = table if args.table is None else args.table
        offset_value = offset if args.offset is None else args.offset
        try:
            # suppress warnig: Workbook contains no default style, apply openpyxl's default
            with warnings.catch_warnings(record=True):
                warnings.simplefilter('always')
                if pathlib.Path(self.file_name).suffix == '.csv':
                    if table_name:
                        log.warning(IGNORED_TABLE)
                    self.data = pd.read_csv(self.file_name, engine=self.engine,
                                            sep=None,   # python engine can detect the separator
                                            skiprows=offset_value, keep_default_na=False)
                elif table_name:
                    self.data = pd.read_excel(self.file_name, engine=self.engine,
                                              sheet_name=table_name, skiprows=offset_value,
                                              keep_default_na=False)
                else:
                    self.data = pd.read_excel(self.file_name, engine=self.engine,
                                              skiprows=offset_value, keep_default_na=False)
        except (OSError, ValueError) as exception:
            log.error(exception)
            log.fatal_error(READING_INPUT_FILE_FAILED)
