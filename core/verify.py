import time
import asyncio
import requests
from threading import Thread, Semaphore
from core.proxies import fetch_proxies
from core.google import wait_for_verification_link
from core.utils import load_file_lines,HEADERS
from data.config import MAX_RETRIES, MAX_THREADS

# Создаем семафор с максимальным количеством потоков
thread_semaphore = Semaphore(MAX_THREADS)

def verify(email, proxy):
    """Процесс верификации"""
    try:
        attempt = 0
        for attempt in range(MAX_RETRIES):
            verification_link = asyncio.run(wait_for_verification_link(email))
            if verification_link:
                requests.get(verification_link, verify=False, headers=HEADERS, proxies=proxy)
                print(f'{email} verified')
                return
            print(f'Verify attempt {attempt + 1}/{MAX_RETRIES}')
            
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