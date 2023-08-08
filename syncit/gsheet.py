""" Google spreadsheet class and operations """
import os
import pickle

from time import sleep

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import pandas as pd

import syncit.logger as log

CREDENTIALS_JSON = 'credentials.json'
GOOGLE_APPLICATION_CREDENTIALS = 'GOOGLE_APPLICATION_CREDENTIALS'
TOKEN_PICKLE = 'token.pickle'
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
WRONG_HEADER = 'wrong header in sheet '

class Gsheet:   # pylint: disable=too-many-instance-attributes
    """ Google spreadsheet class """
    data = {}
    rows = {}
    remove_rows = {}
    active_sheets = []

    def __init__(self, spreadsheet_id, sheets, sheets_config):
        """ Acccess the spreadsheet and read data """
        self.spreadsheet_id = spreadsheet_id
        self.access_spreadsheet()
        self.active_sheets = sheets
        self.sheets_config = sheets_config
        # Get relevant data sheets
        self.get_spreadsheet()

    def access_spreadsheet(self):
        """
        The file token.pickle stores the user's access and refresh tokens,
        and is created automatically when the authorization flow completes
        for the first time.
        Taken from https://developers.google.com/sheets/api/quickstart/python
        """
        log.debug(ACCESS_GOOGLE_SPREADSHEET)
        self.creds = None
        if os.path.exists(TOKEN_PICKLE):
            with open(TOKEN_PICKLE, 'rb') as self.token:
                self.creds = pickle.load(self.token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
                try:
                    self.creds.refresh(Request())
                except:    # pylint: disable=bare-except
                    log.error(SPREADSHEET_CONNECTION_FAILURE)
            else:
                if GOOGLE_APPLICATION_CREDENTIALS in os.environ:
                    credentials_json = os.getenv(GOOGLE_APPLICATION_CREDENTIALS)
                else:
                    credentials_json = CREDENTIALS_JSON
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_json, scopes=SCOPES)
                except (FileNotFoundError, ValueError) as exception:
                    log.error(GOOGLE_CREDENTIALS_JSON_FILE+credentials_json)
                    log.fatal_error(exception)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(TOKEN_PICKLE, 'wb') as self.token:
                pickle.dump(self.creds, self.token)
        try:
            # pylint: disable=no-member
            self.spreadsheet_access = build('sheets', 'v4', credentials=self.creds,
                    cache_discovery=False).spreadsheets()
            log.debug(GOT_GOOGLE_SPREADSHEET_ACCESS)
        except HttpError as error:
            log.error(error)
        # Get attributes
        try:
            spreadsheet = self.spreadsheet_access.get(spreadsheetId=self.spreadsheet_id, ranges=[],
                    includeGridData=False).execute()
            log.debug(GOT_GOOGLE_SPREADSHEET_ATTRIBUTES)
        except HttpError as error:
            log.error(error)
        self.sheet_id = {}
        for sheet in spreadsheet['sheets']:
            self.sheet_id[sheet['properties']['title']] = sheet['properties']['sheetId']

    def get_sheet(self, sheet):
        """ Read the sheet """
        log.debug(READ_GOOGLE_SHEET + sheet)
        try:
            raw_data = self.spreadsheet_access.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=sheet, valueRenderOption='FORMULA').execute().get('values', [])
        except HttpError as error:
            log.error(error)
            return None
        # Normalize raw_data to the same length of the header
        header_offset = self.sheets_config[sheet].header_offset
        try:
            header_length = len(raw_data[header_offset])
        except IndexError:
            log.error(WRONG_HEADER + sheet)
            return None
        for raw in range(header_offset+1, len(raw_data)):
            raw_length = len(raw_data[raw])
            if raw_length < header_length:
                raw_data[raw].extend([''] * (header_length - raw_length))
        # Convert data to pandas format
        return pd.DataFrame(raw_data[header_offset+1:], columns=raw_data[header_offset])

    def get_spreadsheet(self):
        """ Read the active sheets """
        remove_sheets = []
        for sheet in self.active_sheets:
            self.data[sheet] = self.get_sheet(sheet)
            if self.data[sheet] is None:    # empty table without header
                remove_sheets.append(sheet) # sign for removing from active sheets
            else:
                self.remove_rows[sheet] = []
                self.rows[sheet] = len(self.data[sheet].index)
        for sheet in remove_sheets:         # remove signed empty sheets from the next operations
            self.active_sheets.remove(sheet)

    def insert_rows(self, sheet, start_row, inserted_rows):
        """ Insert empty rows in the spreadsheet """
        log.debug(ADD_ROWS_GOOGLE_SHEET + sheet)
        body = {
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": self.sheet_id[sheet],
                            "dimension": "ROWS",
                            "startIndex": start_row,
                            "endIndex": start_row+inserted_rows
                        },
                        "inheritFromBefore": start_row > self.sheets_config[sheet].header_offset + 2
                    }
                }
            ]
        }
        self.request_operation(self.spreadsheet_access.batchUpdate, body)

    def delete_rows(self, sheet, start_row, deleted_rows):
        """ Delete one row in the spreadsheet """
        body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": self.sheet_id[sheet],
                            "dimension": "ROWS",
                            "startIndex": start_row,
                            "endIndex": start_row+deleted_rows
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
            log.debug(UPDATE_GOOGLE_SHEET + sheet)
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
        log.debug(LINK_UPDATE + 'sheet: ' + sheet + ' col: ' + str(column))
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
                            "sheetId": self.sheet_id[sheet],
                            "startRowIndex": header_offset+1,
                            "endRowIndex": len(self.data[sheet].index)+header_offset+1,
                            "startColumnIndex": col,
                            "endColumnIndex": col+1
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
            except HttpError as error:
                if count >= MAX_DELAY_COUNT:
                    log.error(error)
                    return False                    # unsuccessful operation
                sleep(delay)                        # delay in sec
                delay = DELAY_MULTIPLIER * delay    # prolong the next delay
        return False                                # unsuccessful, this way should never happen
