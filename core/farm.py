import asyncio
import time
import httpx
import os
from datetime import datetime
import schedule
import warnings
from urllib3.exceptions import InsecureRequestWarning
from data.config import MAX_THREADS, EXPORT_DATA, MAX_RETRIES
from core.proxies import fetch_proxies_farm
from core.utils import read_tokens
from core.google import save_to_sheet
from pyuseragents import random as random_useragent
import random

os.environ['PYTHONWARNINGS'] = 'ignore:Unverified HTTPS request'

timeout = httpx.Timeout(20.0, connect=20.0, read=120.0, write=20.0)

chrome_extension = {
    'id': 'fpdkjdnhkakefebpekbdhillbhonfjjp',
    'version': '1.0.7'
}

warnings.simplefilter('ignore', InsecureRequestWarning)
user_proxy_map = {}
used_proxies = {}


async def keep_alive(user, proxy):
    url = "https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive"
    headers = {
        "origin": f"chrome-extension://{chrome_extension['id']}",
        "authorization": f"Bearer {user['token']}",
        "content-type": "application/json",
        "user-agent": random_useragent()
    }
    body = {
        "username": user['email'],
        "extensionid": chrome_extension['id'],
        "numberoftabs": 0,
        "_v": chrome_extension['version']
    }

    retries = MAX_RETRIES
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(proxies=proxy, verify=False) as client:
                await client.post(url, headers=headers, json=body, timeout=timeout)
            return  # Exit if successful
        except httpx.ReadTimeout:
            print(f"Timeout in keep_alive for {user['email']} on attempt {attempt + 1}/{retries}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as err:
            print(f"keep_alive request failed for {user['email']}: {err}")
            return -1


async def get_balance(user, proxy):
    url = "https://www.aeropres.in/api/atom/v1/userreferral/getpoint"
    headers = {
        "origin": f"chrome-extension://{chrome_extension['id']}",
        "authorization": f"Bearer {user['token']}",
        "content-type": "application/json",
        "user-agent": random_useragent()
    }

    retries = MAX_RETRIES
    async with httpx.AsyncClient(proxies=proxy, verify=False, timeout=timeout) as client:
        for attempt in range(retries):
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()  # Ensure we catch non-2xx errors
                data = response.json()
                points = sum([
                    data['data']['rewardPoint'].get('points', 0),
                    data['data']['rewardPoint'].get('registerpoints', 0),
                    data['data']['rewardPoint'].get('signinpoints', 0),
                    data['data']['rewardPoint'].get('twitter_x_id_points', 0),
                    data['data']['rewardPoint'].get('discordid_points', 0),
                    data['data']['rewardPoint'].get('telegramid_points', 0),
                    data['data']['referralPoint'].get('commission', 0)
                ])
                return points
            except httpx.ReadTimeout:
                print(f"Timeout in get_balance for {user['email']} on attempt {attempt + 1}/{retries}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as err:
                print(f"Failed to get balance for {user['email']}: {err}")
                return -1
        return -1  # Return -1 if all retries fail


async def get_ip(proxy, user):
    async def fetch_ip():
        async with httpx.AsyncClient(proxies=proxy, verify=False) as client:
            response = await client.get('https://api.ipify.org?format=json', timeout=timeout)
            return response.json()['ip']

    try:
        return await fetch_ip()
    except httpx.ProxyError as err:
        print(f"Proxy error для {user}: {err}.")
        return None
    except Exception as err:
        print(f"Другая ошибка для {user['email']}: {err}")
        raise



def format_date():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


async def get_proxy(user, proxies, user_proxy_map):
    proxy = user_proxy_map.get(user['email'])
    if proxy:
        try:
            user_ip = await get_ip(proxy, user['email'])
            if user_ip:
                print(f"Using another proxy")
                return proxy, user_ip
            else:
                print(f"Existing proxy {proxy} for {user['email']} is not working. Selecting a new one.")
        except Exception as err:
            print(f"Error getting IP for {user['email']} with proxy {proxy}: {err}. Selecting a new one.")

    for attempt in range(MAX_RETRIES):
        proxy = random.choice(proxies)
        user_proxy_map[user['email']] = proxy

        try:
            user_ip = await get_ip(proxy, user['email'])
            if user_ip:
                print(f"Assigned new proxy to {user['email']}")
                return proxy, user_ip
            else:
                print(f"Proxy {proxy} for {user['email']} did not return a valid IP. Retrying...")
        except Exception as err:
            print(f"Error getting IP for {user['email']} with new proxy {proxy}: {err}. Retrying...")

        await asyncio.sleep(2 ** attempt)

    print(f"Failed to assign a working proxy for {user['email']} after {MAX_RETRIES} attempts.")
    return None


    proxy_result = await get_proxy(user, proxies, user_proxy_map)
    if proxy_result is None:
     print(f"Failed to get proxy for {user['email']}")
    else:
        proxy, user_ip = proxy_result


async def farm(user, proxies, print_ip, user_proxy_map, semaphore):
    success = False
    iteration = 0  # Track the iteration count
    while True:
        iteration += 1
        async with semaphore:
            for attempt in range(MAX_RETRIES):
                proxy_result = await get_proxy(user, proxies, user_proxy_map)

                if proxy_result is None:
                    print(f"Failed to get a working proxy for {user['email']} on attempt {attempt + 1}/{MAX_RETRIES}")
                    continue

                proxy, user_ip = proxy_result
                if user_ip:
                    await keep_alive(user, proxy)
                    points = await get_balance(user, proxy) or -1
                    print(f"{user['email']:<40} | {points:.2f} | {format_date():<15} {' | IP: ' + user_ip if user_ip else ''}")

                    if points == -1:
                        user_proxy_map[user['email']] = None
                    else:
                        if iteration % 10 == 1 and EXPORT_DATA:
                            save_to_sheet(user['email'], points, user_ip)
                        success = True
                        break

                print(f"Retrying ping for {user['email']} (Attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(2 ** attempt)

            if not success:
                print(f"All ping attempts failed for {user['email']}")

            await asyncio.sleep(60, 180)


async def start_farming():
    proxies = fetch_proxies_farm()
    if not proxies:
        print("No proxies available.")
        return

    users = read_tokens()
    if not users:
        print("No users with tokens available.")
        return

    if len(proxies) < len(users):
        print("Cant start the code. Users more then proxies")
        return

    # Semaphore to control concurrency
    semaphore = asyncio.Semaphore(len(users))

    # User to proxy mapping
    user_proxy_map = {}

    print(f"Configured {len(proxies)} proxies for {len(users)} users")

    # Start a separate farming task for each user
    tasks = [farm(user, proxies, False, user_proxy_map, semaphore) for user in users]
    await asyncio.gather(*tasks)
