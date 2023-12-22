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


synct.tsheet: Target spreadsheet operations
"""

import numpy
import pandas as pd

class Tsheet:   # pylint: disable=too-many-instance-attributes
    """ Google spreadsheet class """
    data = {}
    rows = {}
    remove_rows = {}
    active_sheets = []
#    sheet_length = {}   # It is needed for delete_rows workaround.

    def __init__(self, config):
        """ Acccess the target spreadsheet and read data """
        self.active_sheets = list(config.sheets.keys())
        self.sheets_config = config.sheets
        # Get relevant data sheets
        self.get_spreadsheet()

    def get_spreadsheet(self):
        """ Read the active sheets of the target spreadsheet """
        remove_sheets = []
        for sheet in self.active_sheets:
            self.get_sheet_data(sheet)
            if self.data[sheet] is None:    # empty table without header
                remove_sheets.append(sheet) # sign for removing from active sheets
            else:
                self.remove_rows[sheet] = []
                self.rows[sheet] = len(self.data[sheet].index)
        for sheet in remove_sheets:         # remove signed empty sheets from the next operations
            self.active_sheets.remove(sheet)

    def get_sheet_data(self, sheet):
        """ Read sheet data from the target spreadsheet """

#    def insert_rows(self, sheet, start_row, inserted_rows):
#        """ Insert empty rows in the target spreadsheet """

    def delete_rows(self, sheet, start_row, deleted_rows):
        """ Delete rows in the target spreadsheet """

    def update_spreadsheet(self):
        """ Update the target spreadsheet data """

    def update_column_with_links(self, sheet, column, link):
        """ Update the column in the target sheet with links """

    def update_data(self, enable_remove):
        """ Update the target spreadsheet """
        self.update_spreadsheet()
        for sheet_name in self.active_sheets:
            for column in self.sheets_config[sheet_name].columns:
                if self.sheets_config[sheet_name].columns[column].link and \
                        self.sheets_config[sheet_name].key == column:
                    self.update_column_with_links(sheet_name, column, \
                            self.sheets_config[sheet_name].columns[column].link)
            if enable_remove and self.remove_rows[sheet_name]:
                removals = {}
                start_row = None
                previous_row = None
                for current_row in sorted(self.remove_rows[sheet_name]):
                    if start_row is None or current_row != previous_row + 1:
                        start_row = current_row
                        previous_row = current_row
                        removals[start_row] = 1
                    else:
                        previous_row = current_row
                        removals[start_row] = removals[start_row] + 1
                for row in sorted(removals, reverse=True):
                    self.delete_rows(sheet_name, \
                            row+self.sheets_config[sheet_name].header_offset+1, removals[row])
        self.save()

    def save(self):
        """ Save the target spreadsheet """

def normalize_type(value):
    """ Avoid numpy type int64 issue that is not allowed in JSON """
    if numpy.issubdtype(type(value), int):
        value = int(value)
    return value

def update_target_row_data(s_sheet, s_key_index, t_sheet, t_row, formula=None):
    """ Update the target row with source data """
    for column in t_sheet.columns:
        if column in s_sheet.data.columns:
            value = normalize_type(s_sheet.data.loc[s_key_index, (column)])
            if value == '' and formula and column in formula:
                value = formula[column]
            t_sheet.loc[t_row, (column)] = value
        else:
            if formula and column in formula:
                value = formula[column]
            else:
                value = ""
            try:
                if pd.isnull(t_sheet.loc[t_row, (column)]):
                    t_sheet.loc[t_row, (column)] = normalize_type(value)   # fix undefined value
            # Fix undefined variable or value issue
            except (KeyError, ValueError):
                t_sheet.loc[t_row, (column)] = normalize_type(value)
