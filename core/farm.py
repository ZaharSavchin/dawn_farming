import asyncio
import time
import aiohttp
import os
from datetime import datetime
import warnings
from urllib3.exceptions import InsecureRequestWarning
from data.config import MAX_THREADS, EXPORT_DATA, MAX_RETRIES, GET_POINTS_RARELY, MIN_SLEEP_TIME, MAX_SLEEP_TIME
from core.proxies import fetch_proxies_aiohttp
from core.utils import read_tokens
from core.google import save_to_sheet
from pyuseragents import random as random_useragent
import random

os.environ['PYTHONWARNINGS'] = 'ignore:Unverified HTTPS request'

timeout = aiohttp.ClientTimeout(total=120, connect=20)

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

    # Validate proxy format
    if not isinstance(proxy, str):
        print(f"Invalid proxy format for {user['email']}: {proxy}")
        return -1

    for attempt in range(MAX_RETRIES):
        try:
            # print(f"keep_alive Attempt {attempt + 1} for {user['email']} using proxy: {proxy}")
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=body, proxy=proxy, ssl=False) as response:
                    if response.status == 200:
                        return  # Exit if successful
        except asyncio.TimeoutError:
            print(f"{'WARNING':<8} | Timeout in keep_alive for {user['email']} on attempt {attempt + 1}/{MAX_RETRIES}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as err:
            print(f"{'ERROR':<8} | keep_alive request failed for {user['email']}: {err}")
    return -1


async def get_balance(user, proxy):
    url = "https://www.aeropres.in/api/atom/v1/userreferral/getpoint"
    headers = {
        "origin": f"chrome-extension://{chrome_extension['id']}",
        "authorization": f"Bearer {user['token']}",
        "content-type": "application/json",
        "user-agent": random_useragent()
    }

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(url, headers=headers, proxy=proxy, ssl=False) as response:
                    if response.status == 200:
                        data = await response.json()
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
            except asyncio.TimeoutError:
                print(f"{'WARNING':<8} | Timeout in get_balance for {user['email']} on attempt {attempt + 1}/{MAX_RETRIES}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as err:
                print(f"{'ERROR':<8} | Failed to get balance for {user['email']}: {err}")
        return -1  # Return -1 if all retries fail


async def get_ip(proxy, user):
    async def fetch_ip():
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get('https://api.ipify.org?format=json', proxy=proxy) as response:
                return (await response.json())['ip']

    try:
        return await fetch_ip()
    except aiohttp.ClientProxyConnectionError as err:
        print(f"{'ERROR':<8} | Proxy error for {user}: {err}.")
        return None
    except Exception as err:
        print(f"{'ERROR':<8} | Other error for {user['email']}: {err}")
        raise

def format_date():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

async def get_proxy(user, proxies, user_proxy_map):
    proxy = user_proxy_map.get(user['email'])
    if proxy:
        try:
            user_ip = await get_ip(proxy, user['email'])
            if user_ip:
                return proxy, user_ip
            else:
                print(f"{'ERROR':<8} | Existing proxy {proxy} for {user['email']} is not working. Selecting a new one.")
        except Exception as err:
            print(f"{'ERROR':<8} | Error getting IP for {user['email']} with proxy {proxy}: {err}. Selecting a new one.")

    for attempt in range(MAX_RETRIES):
        proxy = random.choice(proxies)
        user_proxy_map[user['email']] = proxy

        try:
            user_ip = await get_ip(proxy, user['email'])
            if user_ip:
                print(f"{'INFO':<8} | Changing proxy for {user['email']} with {proxy}")
                return proxy, user_ip
            else:
                print(f"{'WARNING':<8} | Proxy {proxy} for {user['email']} did not return a valid IP. Retrying...")
        except Exception as err:
            print(f"{'ERROR':<8} | Error getting IP for {user['email']} with new proxy {proxy}: {err}. Retrying...")

        await asyncio.sleep(2 ** attempt)
    return None


async def farm(user, proxies, print_ip, user_proxy_map, semaphore):
    iteration = 0  # Track the iteration count

    interval = 10                
    if GET_POINTS_RARELY: 
        interval = 100

    while True:
        sleep_time = random.randint(MIN_SLEEP_TIME, MAX_SLEEP_TIME)
        iteration += 1

        async with semaphore:
            proxy_result = await get_proxy(user, proxies, user_proxy_map)

            if proxy_result is None:
                print(f"{'ERROR':<8} | Failed to get a working proxy for {user['email']}. Skipping...")

            proxy, user_ip = proxy_result
            if user_ip:
                alive_resp = await keep_alive(user, proxy)
                if alive_resp != -1:
                    if iteration % interval == 1:
                        points = await get_balance(user, proxy) or -1
                        print(f"{'SUCCESS':<8} | {user['email']:<40} | {points:.2f} | {format_date():<15} | IP: {user_ip} | sleeping for {sleep_time} seconds...")

                        if points == -1:
                            user_proxy_map[user['email']] = None
                        else:
                            if EXPORT_DATA:
                                save_to_sheet(user['email'], points, user_ip)
                    else:
                        print(f"{'SUCCESS':<8} | {user['email']:<40} | {format_date():<15} | IP: {user_ip} | sleeping for {sleep_time} seconds...")
                else:
                    print(f"{'ERROR':<8} | {user['email']:<40} | {format_date():<15} | Keep alive error")
                    
            await asyncio.sleep(sleep_time)


async def start_farming():
    proxies = fetch_proxies_aiohttp()
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
