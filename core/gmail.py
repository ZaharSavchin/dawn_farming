import base64
import os.path
import asyncio
from data.config import RETRY_DELAY
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = "data/gmail/credentials.json"
TOKEN_PATH = "data/gmail/token-py.json"

def authentificate():
    """Аутентификация в Gmail API."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return creds

def read_email(creds, recipient, process_email):
    """Чтение электронной почты и вызов функции обработки email."""
    try:
        gmail = build("gmail", "v1", credentials=creds)
        res = gmail.users().messages().list(userId='me', q=f'to:{recipient}', maxResults=5).execute()
        messages = res.get('messages', [])
        for message in messages:
            msg = gmail.users().messages().get(userId='me', id=message['id'], format='full').execute()
            print('Snippet:', msg.get('snippet'))
            email_body = msg['payload']['body'].get('data', '')
            if email_body:
                decoded_body = base64.urlsafe_b64decode(email_body.encode('ASCII')).decode('utf-8')
                return process_email(decoded_body)
    except HttpError as error:
        return None

def extract_verification_link(email_body: str) -> str | None:
    """Извлечение ссылки на верификацию из тела письма."""
    start = email_body.find('https://www.aeropres.in/chromeapi/dawn/v1/user/verifylink?key=')
    if start > 0:
        end = email_body.find('</a></p>', start)
        return email_body[start:end]
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
            await asyncio.sleep(RETRY_DELAY)  # Ожидание 3 секунды между попытками
            i += 1
    return verification_link
