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


synct.gsheet: Google spreadsheet access and operations
"""

import os

from stat import S_IRUSR, S_IWUSR

from json.decoder import JSONDecodeError
from time import sleep

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import pandas as pd

import synct.logger as log
from synct.tsheet import Tsheet

CREDENTIALS_JSON = 'credentials.json'
GOOGLE_APPLICATION_CREDENTIALS = 'GOOGLE_APPLICATION_CREDENTIALS'
FILE_PERMISSIONS_MASK = 0o777
TOKEN_JSON = '-token.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Write requests limit handling:
INITIAL_DELAY = 1
DELAY_MULTIPLIER = 2
MAX_DELAY_COUNT = 8

# Debug messages:
ACCESS_GOOGLE_SPREADSHEET = 'access Google spreadsheet'
ADD_ROWS_GOOGLE_SHEET = 'add rows in Google sheet: '
GOT_GOOGLE_SPREADSHEET_ACCESS = 'got Google spreadsheet access'
GOT_GOOGLE_SPREADSHEET_ATTRIBUTES = 'got Google spreadsheet attributes'
LINK_UPDATE = 'link update: '
READ_GOOGLE_SHEET = 'read Google sheet: '
UPDATE_GOOGLE_SHEET = 'update Google sheet: '

# Error messages:
SPREADSHEET_CONNECTION_FAILURE = 'failed to establish Google spreadsheet connection'
GOOGLE_CREDENTIALS_JSON_FILE = 'Google credentials JSON file: '
GOOGLE_TOKEN_FILE = 'Google token file: '
WRONG_HEADER = 'wrong header in the sheet '
WRONG_HEADER_OFFSET = 'header offset could be wrong in the sheet '
GOOGLE_AUTHORIZATION_ERROR = 'Google authorization error'
INSUFFICIENT_TOKEN = 'Insufficient Google token file: '

class Gsheet(Tsheet):   # pylint: disable=too-many-instance-attributes
    """ Google spreadsheet class """

    def __init__(self, config):
        """ Acccess the spreadsheet and read data """
        self.spreadsheet_id = config.spreadsheet_id
        self.access_spreadsheet()
        Tsheet.__init__(self, config)

    def access_spreadsheet(self):
        """
        The file token.json stores the user's access and refresh tokens,
        and is created automatically when the authorization flow completes
        for the first time.
        Taken from https://developers.google.com/sheets/api/quickstart/python
        """
        log.debug(ACCESS_GOOGLE_SPREADSHEET)
        creds = None
        (credentials_json, credentials_mode, token_json) = get_cred_files()
        if os.path.exists(token_json):
            try:
                creds = Credentials.from_authorized_user_file(token_json, SCOPES)
            except JSONDecodeError:
                pass
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError as error:
                    log.error(GOOGLE_AUTHORIZATION_ERROR)
                    log.error(error)
                    log.fatal_error(INSUFFICIENT_TOKEN + token_json)
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_json, scopes=SCOPES)
                except (FileNotFoundError, ValueError) as exception:
                    log.error(GOOGLE_CREDENTIALS_JSON_FILE+credentials_json)
                    log.fatal_error(exception)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            try:
                with open(token_json, 'w', encoding='utf-8') as token:
                    # Set token permissions
                    os.chmod(token_json, credentials_mode | S_IRUSR | S_IWUSR)
                    # Write the token
                    token.write(creds.to_json())
            except OSError as exception:
                log.error(GOOGLE_TOKEN_FILE+token_json)
                log.fatal_error(exception)
        try:
            # pylint: disable=no-member
            self.spreadsheet_access = build('sheets', 'v4', credentials=creds,
                    cache_discovery=False).spreadsheets()
            log.debug(GOT_GOOGLE_SPREADSHEET_ACCESS)
        except (HttpError, TimeoutError) as error:
            log.fatal_error(error)
        # Get attributes of the spreadsheet
        try:
            spreadsheet = self.spreadsheet_access.get(spreadsheetId=self.spreadsheet_id, ranges=[],
                    includeGridData=False).execute()
            log.debug(GOT_GOOGLE_SPREADSHEET_ATTRIBUTES)
        except (HttpError, TimeoutError) as error:
            log.fatal_error(error)
        except RefreshError as error:
            log.error(GOOGLE_AUTHORIZATION_ERROR)
            log.error(error)
            log.fatal_error(INSUFFICIENT_TOKEN + token_json)
        self.sheet_id = {}
        for sheet in spreadsheet['sheets']:
            self.sheet_id[sheet['properties']['title']] = sheet['properties']['sheetId']

    def get_sheet_data(self, sheet):
        """ Read sheet data """
        log.debug(READ_GOOGLE_SHEET + "'" + sheet + "'")
        self.data[sheet] = None
        try:
            raw_data = self.spreadsheet_access.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=sheet, valueRenderOption='FORMULA').execute().get('values', [])
        except (HttpError, TimeoutError) as error:
            log.error(error)
            return
        # Normalize raw_data to the same length of the header
        header_offset = self.sheets_config[sheet].header_offset
        try:
            header_length = len(raw_data[header_offset])
        except IndexError:
            log.error(WRONG_HEADER + "'" + sheet + "'")
            return
        for raw in range(header_offset+1, len(raw_data)):
            raw_length = len(raw_data[raw])
            if raw_length < header_length:
                raw_data[raw].extend([''] * (header_length - raw_length))
        # Convert data to pandas format
        try:
            self.data[sheet] = pd.DataFrame(raw_data[header_offset+1:], \
                    columns=raw_data[header_offset])
        except ValueError as exception:
            log.error(exception)
            log.fatal_error(WRONG_HEADER_OFFSET + "'" + sheet + "'")

#        self.sheet_length[sheet] = len(self.data[sheet])   # not needed, it is required by ysheet

    def insert_rows(self, sheet, start_row, inserted_rows):
        """ Insert empty rows in the spreadsheet """
        log.debug(ADD_ROWS_GOOGLE_SHEET + "'" + sheet + "'")
        body = {
            'requests': [
                {
                    'insertDimension': {
                        'range': {
                            'sheetId': self.sheet_id[sheet],
                            'dimension': 'ROWS',
                            'startIndex': start_row,
                            'endIndex': start_row+inserted_rows
                        },
                        'inheritFromBefore': start_row > self.sheets_config[sheet].header_offset + 2
                    }
                }
            ]
        }
        self.request_operation(self.spreadsheet_access.batchUpdate, body)

    def delete_rows(self, sheet, start_row, deleted_rows):
        """ Delete rows in the spreadsheet """
        body = {
            'requests': [
                {
                    'deleteDimension': {
                        'range': {
                            'sheetId': self.sheet_id[sheet],
                            'dimension': 'ROWS',
                            'startIndex': start_row,
                            'endIndex': start_row+deleted_rows
                        }
                    }
                }
            ]
        }
        self.request_operation(self.spreadsheet_access.batchUpdate, body)

    def update_spreadsheet(self):
        """ Update the Google spreadsheet data without header """
        for sheet in self.active_sheets:
            if len(self.data[sheet].index) > self.rows[sheet]:
                self.insert_rows(sheet, \
                        self.sheets_config[sheet].header_offset+self.rows[sheet]+2, \
                        len(self.data[sheet])-self.rows[sheet])
            log.debug(UPDATE_GOOGLE_SHEET + "'" + sheet + "'")
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': [
                       {
                            'range': sheet+'!A'+str(self.sheets_config[sheet].header_offset+2),
                            'majorDimension': 'ROWS',
                            'values': self.data[sheet].values.tolist()
                        }
                    ]
                }
            if not self.request_operation(self.spreadsheet_access.values().batchUpdate, body):
                return

    def update_column_with_links(self, sheet, column, link):
        """ Update the column in the Google sheet with links """
        log.debug(LINK_UPDATE + 'sheet: ' + "'" + sheet + "'" + ' col: ' + str(column))
        header_offset = self.sheets_config[sheet].header_offset
        col = self.data[sheet].columns.get_loc(column)
        rows = []
        for row in self.data[sheet].index:
            rows.append({'values': {'userEnteredFormat': {'textFormat': {'link': {'uri': \
                        link + str(self.data[sheet][column][row])}}}}})
        body = {
            'requests': [
                {
                    'updateCells': {
                        'rows': rows,
                        'fields': 'userEnteredFormat.textFormat.link.uri',
                        'range': {
                            'sheetId': self.sheet_id[sheet],
                            'startRowIndex': header_offset+1,
                            'endRowIndex': len(self.data[sheet].index)+header_offset+1,
                            'startColumnIndex': col,
                            'endColumnIndex': col+1
                        }
                    }
                }
            ]
        }
        self.request_operation(self.spreadsheet_access.batchUpdate, body)

    def request_operation(self, operation, body):
        """
        Handle batchUpdate request with preventing to exceed the limit of
        'Write requests per minute per user'. If the request is not successful,
        it is repeated with a delay more times. The delay value is increased
        exponentially in the next round.
        """
        delay = INITIAL_DELAY                       # the initial delay after the first error
        count = 0                                   # counter of the operation requests
        while count < MAX_DELAY_COUNT:
            count = count + 1
            try:
                response = operation(
                        spreadsheetId=self.spreadsheet_id, body=body).execute()
                log.debug(response)
                return True                         # successful operation
            except (HttpError, TimeoutError) as error:
                if count >= MAX_DELAY_COUNT:
                    log.error(error)
                    return False                    # unsuccessful operation
                sleep(delay)                        # delay in sec
                delay = DELAY_MULTIPLIER * delay    # prolong the next delay
        return False                                # unsuccessful, this way should never happen

def get_cred_files():
    """
    Get credentials and token file names. The token file name is derived
    from the credentials file name including the same path and permissions.
    """
    if GOOGLE_APPLICATION_CREDENTIALS in os.environ:
        credentials_json = os.getenv(GOOGLE_APPLICATION_CREDENTIALS)
    else:
        credentials_json = CREDENTIALS_JSON
    credentials_json = os.path.expanduser(credentials_json)
    credentials_json_status = os.stat(credentials_json)
    (root, ext) = os.path.splitext(credentials_json)    # pylint: disable=unused-variable
    token_json = root + TOKEN_JSON
    return (credentials_json, credentials_json_status.st_mode & FILE_PERMISSIONS_MASK, token_json)
