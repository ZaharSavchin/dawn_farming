from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


CREDENTIALS_PATH = "data/gmail/main/service-credentials.json"

executor = ThreadPoolExecutor(max_workers=5)

class ExportSheet:
    def __init__(self, spreadsheet_id: str, sheet: str):
        self.spreadsheet_id = spreadsheet_id
        self.sheet = sheet

def initialize_sheets_service(key_file: str):
    credentials = service_account.Credentials.from_service_account_file(
        key_file,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=credentials)

def export_points(export_sheet: ExportSheet, user: str, points: float, group: Optional[str] = None):
    
    with executor:
      sheets_service = initialize_sheets_service(CREDENTIALS_PATH)
      start_index = 4

      data = sheets_service.spreadsheets().values().batchGet(
          spreadsheetId=export_sheet.spreadsheet_id,
          ranges=[f"{export_sheet.sheet}!A{start_index}:A1000"]
      ).execute()

      values: List[List[str]] = data.get('valueRanges', [{}])[0].get('values', [])
      found = False
      time_now = datetime.utcnow().isoformat(sep=' ', timespec='seconds')

      for i, row in enumerate(values):
          if row:
              email = row[0]
              if email == user:
                  found = True
                  sheets_service.spreadsheets().values().update(
                      spreadsheetId=export_sheet.spreadsheet_id,
                      range=f"{export_sheet.sheet}!B{start_index + i}:D{start_index + i}",
                      valueInputOption='USER_ENTERED',
                      body={
                          'values': [[int(points), time_now, group or '']]
                      }
                  ).execute()

      if not found:
          row = start_index + len(values)
          sheets_service.spreadsheets().values().update(
              spreadsheetId=export_sheet.spreadsheet_id,
              range=f"{export_sheet.sheet}!A{row}:D{row}",
              valueInputOption='USER_ENTERED',
              body={
                  'values': [[user, int(points), time_now, group or '']]
              }
          ).execute()
