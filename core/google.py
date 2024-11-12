import base64
import os.path
import asyncio
import re
from datetime import datetime
from data.config import RETRY_DELAY
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from data.config import SHEET_ID, LIST_NAME

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", 'https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_PATH = "data/google/credentials.json"
TOKEN_PATH = "data/google/token-py.json"

def authentificate():
    """Аутентификация в Google API."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            print(f"Ошибка при чтении токена: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Сохранение нового токена
        if creds:
            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())
            print("Токен успешно сохранен в token-py.json")
        else:
            print("Ошибка аутентификации. Токен не был получен.")
    return creds

def read_email(creds, recipient, process_email):
    """Чтение электронной почты и вызов функции обработки email."""
    try:
        gmail = build("gmail", "v1", credentials=creds)
        res = gmail.users().messages().list(userId='me', q=f'to:{recipient}', maxResults=5).execute()
        messages = res.get('messages', [])
        for message in messages:
            msg = gmail.users().messages().get(userId='me', id=message['id'], format='full').execute()
            print(f'Link found for {recipient}')
            email_body = msg['payload']['body'].get('data', '')
            if email_body:
                decoded_body = base64.urlsafe_b64decode(email_body.encode('ASCII')).decode('utf-8')
                return process_email(decoded_body)
    except HttpError as error:
        return None

def extract_verification_link(email_body: str) -> str | None:
    """Извлечение ссылки на верификацию из тела письма."""
    pattern = r'<a href="(https://.*?\.sendgrid\.net/ls/click.*?)"><button'
    match = re.search(pattern, email_body)
    if match:
        return match.group(1)
    return None

async def wait_for_verification_link(email: str) -> str | None:
    """Ожидание ссылки на верификацию в письме."""
    creds = authentificate()
    max_tries = 60
    verification_link = None
    i = 0
    while verification_link is None and i < max_tries:
        verification_link = read_email(creds, email, extract_verification_link)
        if verification_link is None:
            await asyncio.sleep(RETRY_DELAY)
            i += 1
    return verification_link

def save_to_sheet(username, points, ip):
    creds = authentificate()
    spreadsheet_id = SHEET_ID
    current_time = datetime.now()
    time = current_time.strftime("%d.%m.%Y | %H:%M")
    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # Get all values in the sheet
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=f"{LIST_NAME}!A:D").execute()
        rows = result.get('values', [])
        
        # Find the row to update
        row_to_update = None
        for i, row in enumerate(rows):
            if row and row[0] == username:  # Username column is the first column
                row_to_update = i + 1  # Rows are 1-indexed in Google Sheets API
                break
        
        if row_to_update:
            # Update the existing row
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{LIST_NAME}!A{row_to_update}:D{row_to_update}",
                valueInputOption="RAW",
                body={"values": [[username, points, ip, time]]}
            ).execute()
        else:
            # Append a new row
            sheet.values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{LIST_NAME}!A:D",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [[username, points, ip, time]]}
            ).execute()

    except HttpError as error:
        print(f"An error occurred with {username} in GSheet: {error}")