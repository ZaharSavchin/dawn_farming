import asyncio
import time
import httpx
import os
from datetime import datetime
import schedule
import warnings
from urllib3.exceptions import InsecureRequestWarning
from data.config import MAX_THREADS, EXPORT_DATA
from core.proxies import fetch_proxies_farm
from core.utils import read_tokens
from core.google import save_to_sheet
from pyuseragents import random as random_useragent
import random

# Disable TLS warnings (not recommended for production)
os.environ['PYTHONWARNINGS'] = 'ignore:Unverified HTTPS request'

timeout = httpx.Timeout(10.0, connect=10.0, read=15.0, write=10.0)

chrome_extension = {
    'id': 'fpdkjdnhkakefebpekbdhillbhonfjjp',
    'version': '1.0.7'
}

warnings.simplefilter('ignore', InsecureRequestWarning)
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

    async with httpx.AsyncClient(proxies=proxy, verify=False) as client:
        try:
            await client.post(url, headers=headers, json=body)
        except Exception as err:
            print(f"keepAlive request failed for {user['email']}: {err}")
            raise

async def get_balance(user, proxy):
    url = "https://www.aeropres.in/api/atom/v1/userreferral/getpoint"
    headers = {
        "origin": f"chrome-extension://{chrome_extension['id']}",
        "authorization": f"Bearer {user['token']}",
        "content-type": "application/json",
        "user-agent": random_useragent()
    }

    async with httpx.AsyncClient(proxies=proxy, verify=False) as client:
        try:
            response = await client.get(url, headers=headers)
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
        except Exception as err:
            raise

async def get_ip(proxy, user):
    try:
        async with httpx.AsyncClient(proxies=proxy, verify=False) as client:
            response = await client.get('https://api.ipify.org?format=json')
            return response.json()['ip']
    except Exception as err:
        print(f"Can't get IP for {user}")
        raise

async def with_retry(name, code, retries=0):
    if retries < 5:
        try:
            return await code()
        except:
            await asyncio.sleep(0.5)
            print(f"Retrying {retries} ({name})...")
            return await with_retry(name, code, retries + 1)
    else:
        print(f"Reached max retries for {name}")
        return None

async def find_available_proxy(user_id, proxies, print_ip=False):
    proxy_url = find_key_by_value(used_proxies, user_id)
    if proxy_url is not None:
        next_proxy = {
            'http://': proxy_url,
            'https://': proxy_url
        }
    else:
        # Find a proxy whose URL is not yet used
        next_proxy = next((p for p in proxies if p['http://'] not in used_proxies), None)

    if next_proxy:
        proxy = next_proxy
        ip = await with_retry('getIP', lambda: get_ip(proxy, user_id))
        if ip is not None:
            # Use the 'http://' key as the hashable identifier for the proxy
            proxy_key = next_proxy['http://']
            used_proxies[proxy_key] = user_id
            if print_ip:
                print(f'user {user_id} got {ip}')
            return proxy
        else:
            print(f'No IP for {user_id}. Next loop')
            used_proxies[next_proxy['http://']] = None
            return await find_available_proxy(user_id, proxies)
    else:
        print("No available proxies")
        return None

def find_key_by_value(my_dict, target_value):
    for key, value in my_dict.items():
        if value == target_value:
            return key
    return None  # Return None if the value is not found

async def reserve_proxies(users, proxies): 
    start_time = time.time()
    for user in users:
        await find_available_proxy(user['email'], proxies, print_ip = True)

    print(f"\nIt took: {((time.time()  - start_time) / 60):.2f} minutes to find proxies {len(users)} users\n") 

async def cleanup_proxies():
    before_clean_up = len(used_proxies)
    for proxy, user_id in list(used_proxies.items()):
        if user_id is None:
            del used_proxies[proxy]
    after_clean_up = len(used_proxies)
    print(f"Cleaned up {before_clean_up - after_clean_up} proxies")

def format_date():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

async def farm(user, proxies, print_ip):
    proxy = await find_available_proxy(user['email'], proxies, print_ip)
    if proxy:
        user_ip = await get_ip(proxy, user['email'])
        await with_retry('keepAlive', lambda: keep_alive(user, proxy))
        points = await with_retry('getBalance', lambda: get_balance(user, proxy)) or -1
        print(f"{user['email']:<40} | {points:.2f} | {format_date():<15} {' | IP: ' + user_ip}")
        if points == -1:
            used_proxies[proxy['http://']] = None
            await farm(user, proxies, print_ip=True)
        else:
            if EXPORT_DATA:
                save_to_sheet(user['email'], points, user_ip)
    else:
        print(f"Can't find a proxy for {user['email']}")
        await cleanup_proxies()
        await farm(user, proxies, print_ip)

async def farm_for_all(users, proxies, n_tasks, print_ip):
    start_time = time.time()
    tasks = [farm(user, proxies, print_ip) for user in users[:n_tasks]]
    await asyncio.gather(*tasks)
    print(f"\nIt took: {((time.time() - start_time) / 60):.2f} minutes to farm points for {len(users)} users\n")

async def start_farming():
    proxies = fetch_proxies_farm()
    if not proxies:
        print("No proxies available.")
        return

    users = read_tokens()
    if not users:
        print("No users with tokens available.")
        return
    

    print(f"Configured {len(proxies)} proxies for {len(users)} users")
    await reserve_proxies(users, proxies)
    await farm_for_all(users, proxies, len(users), False)

    while True:
        await farm_for_all(users, proxies, len(users), False)
        await asyncio.sleep(5)