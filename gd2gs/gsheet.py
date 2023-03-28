""" Google spreadsheet class and operations """
import os
import pickle

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import pandas as pd

import gd2gs.logger as log

CREDENTIALS_JSON = 'credentials.json'
GOOGLE_APPLICATION_CREDENTIALS = 'GOOGLE_APPLICATION_CREDENTIALS'
TOKEN_PICKLE = 'token.pickle'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SPREADSHEET_CONNECTION_FAILURE = 'failed to establish Google spreadsheet connection'

DATA_SHEET = 'Data Sheet'

class Gsheet:   # pylint: disable=too-many-instance-attributes
    """ Google spreadsheet class """
    data = {}
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
        log.debug('access Google spreadsheet')
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
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_json, scopes=SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(TOKEN_PICKLE, 'wb') as self.token:
                pickle.dump(self.creds, self.token)
        try:
            # pylint: disable=no-member
            self.spreadsheet_access = build('sheets', 'v4', credentials=self.creds,
                    cache_discovery=False).spreadsheets()
            log.debug('got Google spreadsheet access')
        except HttpError as error:
            log.error(error)
        # Get attributes
        try:
            spreadsheet = self.spreadsheet_access.get(spreadsheetId=self.spreadsheet_id, ranges=[],
                    includeGridData=False).execute()
            log.debug('got Google spreadsheet attributes')
        except HttpError as error:
            log.error(error)
        self.sheet_id = {}
        for sheet in spreadsheet['sheets']:
            self.sheet_id[sheet['properties']['title']] = sheet['properties']['sheetId']

    def get_sheet(self, sheet):
        """ Read the sheet """
        log.debug('read Google sheet: ' + sheet)
        try:
            raw_data = self.spreadsheet_access.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=sheet, valueRenderOption='FORMULA').execute().get('values', [])
        except HttpError as error:
            log.error(error)
            return None
        # Normalize raw_data to the same length of the header
        header_offset = self.sheets_config[sheet].header_offset
        header_length = len(raw_data[header_offset])
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
            data = self.get_sheet(sheet)
            if data is not None:
                self.data[sheet] = data
            else:            # the sheet is not available
                log.error("can't access sheet " + sheet)
                remove_sheets.append(sheet)
        for sheet in remove_sheets:
            self.active_sheets.remove(sheet)

    def update_spreadsheet(self):
        """ Update the Google spreadsheet data without header """
        for sheet in self.active_sheets:
            log.debug('update Google sheet: ' + sheet)
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
            try:
                response = self.spreadsheet_access.values().batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body=body).execute()
                log.debug(response)
            except HttpError as error:
                log.error(error)
                return

    def update_column_with_links(self, sheet, column, link):
        """ Update the column in the Google sheet with links """
        log.debug('link update: sheet: ' + sheet + ' col: ' + str(column))
        header_offset = self.sheets_config[sheet].header_offset
        col = self.data[sheet].columns.get_loc(column)
        rows = []
        for row in range(self.data[sheet].index.start,
                         self.data[sheet].index.stop,
                         self.data[sheet].index.step):
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
                            "startRowIndex": self.data[sheet].index.start+header_offset+1,
                            "endRowIndex": self.data[sheet].index.stop+header_offset+1,
                            "startColumnIndex": col,
                            "endColumnIndex": col+1
                        }
                    }
                }
            ]
        }
        try:
            response = self.spreadsheet_access.batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body).execute()
            log.debug(response)
        except HttpError as error:
            log.error(error)
