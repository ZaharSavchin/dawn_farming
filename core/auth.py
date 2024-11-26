import time
import asyncio
import requests
from threading import Thread, Semaphore 
from core.boost import boost_user
from core.proxies import fetch_proxies
from core.google import wait_for_verification_link
from core.utils import load_file_lines, save_token_to_file, make_request, HEADERS, test_proxy, save_token_to_db
from core.captcha import solve_captcha
from data.config import MAX_RETRIES, RETRY_DELAY, REGISTER, MAX_THREADS, REF_CODE, BOOST_USERS

# Создаем семафор с максимальным количеством потоков
thread_semaphore = Semaphore(MAX_THREADS)

APP_ID = "66fa9fc4bc2ec041135db33b"
REGISTER_URL = 'https://www.aeropres.in/chromeapi/dawn/v1/puzzle/validate-register'
LOGIN_URL = 'https://www.aeropres.in/chromeapi/dawn/v1/user/login/v2'
PUZZLE_URL = 'https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle'
PUZZLE_IMAGE_URL = 'https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle-image'

def process_user(user_data, proxy):
    """Процесс регистрации и логина для одного пользователя (синхронный)."""
    try:
        attempt = 0
        for attempt in range(MAX_RETRIES):
            puzzle_id, puzzle_image_base64 = fetch_puzzle(proxy)
            if not puzzle_id or not puzzle_image_base64:
                print(f"Не удалось получить пазл для {user_data['email']}")
                continue

            # Используем asyncio.run() для запуска solve_captcha
            puzzle_ans =  asyncio.run(solve_captcha(puzzle_image_base64))
            if not puzzle_ans:
                print(f"Не удалось решить капчу для {user_data['email']}")
                continue
            
            if REGISTER:
                # Регистрация
                reg_response = register_user(user_data, puzzle_ans, puzzle_id, proxy)
                if reg_response == 'already registered':
                    return
                if reg_response and reg_response.get('success'):
                    print(f"Регистрация успешна для {user_data['email']}!")
                    # Используем asyncio.run() для запуска wait_for_verification_link
                    verification_link = asyncio.run(wait_for_verification_link(user_data['email']))
                    if verification_link:
                        requests.get(verification_link, verify=False, headers=HEADERS, proxies=proxy)

                        # Логин
                        login_attempt = 0
                        for login_attempt in range(MAX_RETRIES):
                            puzzle_id, puzzle_image_base64 = fetch_puzzle(proxy)
                            if not puzzle_id or not puzzle_image_base64:
                                print(f"Не удалось получить пазл для {user_data['email']}")
                                continue

                            # Используем asyncio.run() для запуска solve_captcha
                            puzzle_ans =  asyncio.run(solve_captcha(puzzle_image_base64))
                            if not puzzle_ans:
                                print(f"Не удалось решить капчу для {user_data['email']}")
                                continue

                            login_response = login_user(user_data, puzzle_ans, puzzle_id, proxy)
                            if login_response == 'not registered':
                                return
                            if login_response and login_response.get('data', {}).get('token'):
                                token = login_response['data']['token']
                                user_data['token'] = token

                                print(f'user_data = {user_data}')

                                save_token_to_file(user_data['email'], token)
                                save_token_to_db(email=user_data['email'], password=user_data['password'], token=token)

                                user = {
                                    'email': user_data['email'],
                                    'token': token,
                                }
                                if BOOST_USERS:
                                    boost_user(user, proxy)
                                return
                            print(f'Login attempt {login_attempt + 1}/{MAX_RETRIES}')
                        print(f"Максимальное количество попыток для {user_data['email']}")
                    else:
                        print(f"Не удалось получить ссылку на верификацию для {user_data['email']}")

                else:
                    print(f"Ошибка регистрации для {user_data['email']}")
            else:
                # Логин
                login_response = login_user(user_data, puzzle_ans, puzzle_id, proxy)
                if login_response == 'not registered':
                    return
                if login_response and login_response.get('data', {}).get('token'):
                    token = login_response['data']['token']
                    user_data['token'] = token

                    save_token_to_file(user_data['email'], token)
                    save_token_to_db(email=user_data['email'], password=user_data['password'], token=token)

                    user = {
                        'email': user_data['email'],
                        'token': token,
                    }
                    if BOOST_USERS:
                        boost_user(user, proxy)
                    return
        print(f"Максимальное количество попыток для {user_data['email']}")
    finally:
        # Обязательно освобождаем семафор, чтобы следующие потоки могли начать
        thread_semaphore.release()

def process_users():
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
            username = email.split('@')[0]
            user_data = {
                "fullname": username,
                "email": email,
                "password": password,
                "refer_code": REF_CODE,
                "mobile": ""
            }
            proxy = proxies.pop(0) if proxies else None

            # Ждем, пока не освободится место для нового потока
            thread_semaphore.acquire()

            # Создание потока для каждого пользователя
            thread = Thread(target=process_user, args=(user_data, proxy))
            threads.append(thread)
            thread.start()

        except ValueError:
            print(f"Пропущена неверная запись пользователя: {line}")

    # Ожидание завершения всех потоков
    for thread in threads:
        thread.join()

def fetch_puzzle(proxy=None):
    """Получение пазла для капчи."""
    puzzle_data = make_request(f"{PUZZLE_URL}?appid={APP_ID}", proxy)
    if puzzle_data:
        puzzle_id = puzzle_data.get('puzzle_id')
        image_data = make_request(f"{PUZZLE_IMAGE_URL}?puzzle_id={puzzle_id}&appid={APP_ID}", proxy)
        if image_data:
            return puzzle_id, image_data.get('imgBase64')
    return None, None

def register_user(user_data, puzzle_ans, puzzle_id, proxy=None):
    """Отправка запроса на регистрацию."""
    registration_data = {
        "firstname": user_data["fullname"],
        "lastname": user_data["fullname"],
        "email": user_data["email"],
        "mobile": user_data["mobile"],
        "password": user_data["password"],
        "country": "+91",
        "referralCode": user_data["refer_code"],
        "puzzle_id": puzzle_id,
        "ans": puzzle_ans
    }
    return make_request(f"{REGISTER_URL}?appid={APP_ID}", proxy, method='POST', data=registration_data)

def login_user(user_data, puzzle_ans, puzzle_id, proxy=None):
    """Отправка запроса на логин."""
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"],
        "logindata": {"_v": "1.0", "datetime": time.strftime("%Y-%m-%d %H:%M:%S")},
        "puzzle_id": puzzle_id,
        "ans": puzzle_ans
    }
    return make_request(f"{LOGIN_URL}?appid={APP_ID}", proxy, method='POST', data=login_data)