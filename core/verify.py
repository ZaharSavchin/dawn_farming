import time
import asyncio
import requests
from threading import Thread, Semaphore
from core.proxies import fetch_proxies
from core.google import wait_for_verification_link
from core.utils import load_file_lines, HEADERS, make_request
from data.config import MAX_RETRIES, MAX_THREADS
from core.auth import fetch_puzzle
from core.captcha import solve_captcha
import json

# Создаем семафор с максимальным количеством потоков
thread_semaphore = Semaphore(MAX_THREADS)

APP_ID = "66fa9fc4bc2ec041135db33b"
PUZZLE_URL = 'https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle'
PUZZLE_IMAGE_URL = 'https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle-image'
RESEND_URL = 'https://www.aeropres.in/chromeapi/dawn/v1/user/resendverifylink/v2'


def resend_email(email, proxy, puzzle_ans, puzzle_id):
    """Send request for resending email"""
    resend_data = {
        "username": email,
        "puzzle_id": puzzle_id,
        "ans": puzzle_ans
    }
    response = requests.post(f"{RESEND_URL}?appid={APP_ID}", headers=HEADERS, data=json.dumps(resend_data), proxies=proxy, verify=False)
    payload = response.text
    return json.loads(payload)

def verify(email, proxy):
    """Процесс верификации"""
    try:
        attempt = 0
        for attempt in range(MAX_RETRIES):
            puzzle_id, puzzle_image_base64 = fetch_puzzle(proxy)
            if not puzzle_id or not puzzle_image_base64:
                print(f"Не удалось получить пазл для {email}")
                continue

            # Используем asyncio.run() для запуска solve_captcha
            puzzle_ans =  asyncio.run(solve_captcha(puzzle_image_base64))
            if not puzzle_ans:
                print(f"Не удалось решить капчу для {email}")
                continue

            response = resend_email(email, proxy, puzzle_ans, puzzle_id)
            print(response)
            if response and response['message'] == 'verification link sent to email':
                print("Email resent successfully. Waiting for verification link")
                verification_link = asyncio.run(wait_for_verification_link(email))
                if verification_link:
                    requests.get(verification_link, verify=False, headers=HEADERS, proxies=proxy)
                    print(f'{email} verified')
                    return
                print(f'Verify attempt {attempt + 1}/{MAX_RETRIES}')
            else:                
                print(f'Resend attempt for {email} {attempt + 1}/{MAX_RETRIES}')
                continue
            
        print(f"Максимальное количество попыток для {email}")
    finally:
        # Обязательно освобождаем семафор, чтобы следующие потоки могли начать
        thread_semaphore.release()

def verify_users():
    """Чтение списка пользователей и запуск потоков для каждого пользователя."""
    users = load_file_lines('data/users.txt')
    proxies = fetch_proxies()

    if len(users) > len(proxies):
        print("Ошибка: больше пользователей, чем доступных прокси.")
        return

    threads = []  # Список для хранения потоков
    for line in users:
        try:
            email, password = line.split(':')
            proxy = proxies.pop(0) if proxies else None

            # Ждем, пока не освободится место для нового потока
            thread_semaphore.acquire()

            # Создание потока для каждого пользователя
            thread = Thread(target=verify, args=(email, proxy))
            threads.append(thread)
            thread.start()

        except ValueError:
            print(f"Пропущена неверная запись пользователя: {line}")

    # Ожидание завершения всех потоков
    for thread in threads:
        thread.join()
