import requests
import json
import time
import warnings
from urllib3.exceptions import InsecureRequestWarning
from data.config import RETRY_DELAY

HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

# Check if proxy is working before login
def test_proxy(proxy):
    try:
        response = requests.get('https://api.ipify.org?format=json', proxies=proxy, timeout=5)
        ip = response.json()['ip']
        return ip  
    except Exception:
        return None

def load_file_lines(file_path):
    """Чтение строк из файла."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return []

def read_tokens():
    """Загрузка списка юзеров из файла."""
    users = []
    lines = load_file_lines('data/tokens.txt')
    for line in lines:
        try:
            email, token = line.split(':')
            users.append({'email': email, 'token': token})
        except ValueError:
            print(f"Неверный формат прокси: {line}")
    return users

def save_token_to_file(email, token):
    """Сохранение токена в файл."""
    with open('data/tokens.txt', 'a', encoding='utf-8') as f:
        f.write(f"{email}:{token}\n")
    print(f"Token saved for {email}")

def save_not_extracted_account(email, password):
    """Сохранение данных в файл."""
    with open('data/not-valid.txt', 'a', encoding='utf-8') as f:
        f.write(f"{email}:{password}\n")
    print(f"Not saved for {email}")

def save_not_registered_accounts(email):
    """Сохранение данных в файл."""
    with open('data/not-registred.txt', 'a', encoding='utf-8') as f:
        f.write(f"{email}\n")
    print(f"Not registred or invalid data {email}")

def make_request(url, proxy=None, method='GET', data=None):
    """Отправка HTTP-запросов с повторами."""
    try:
        if method == 'POST':
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', InsecureRequestWarning)
                print(f"Sending POST request to {url} with data: {data}")
                response = requests.post(url, headers=HEADERS, data=json.dumps(data), proxies=proxy, verify=False)
        else:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', InsecureRequestWarning)
                print(f"Sending GET request to {url}")
                response = requests.get(url, headers=HEADERS, proxies=proxy, verify=False)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.ProxyError as e:
        print(f"Proxy error: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {e}")
        print(f"Response text: {response.text}")  # This can give clues about the error
        response_data = response.json()
        if 'message' in response_data:
            if response_data['message'] == 'Invalid username or Password!':
                save_not_registered_accounts(data['username'])
                return 'not registered'
        time.sleep(RETRY_DELAY)
    except requests.exceptions.RequestException as e:
        print(f"Error during {method} request to {url}: {e}")
        time.sleep(RETRY_DELAY)
    return None