import asyncio
import time
import httpx
import requests
import os
from datetime import datetime
import schedule
import threading
import warnings
from urllib3.exceptions import InsecureRequestWarning
from data.config import MAX_THREADS, EXPORT_DATA
from core.proxies import fetch_proxies_farm
from core.utils import read_tokens
from core.google import save_to_sheet

find_proxy_lock = threading.Lock()

timeout = httpx.Timeout(10.0, connect=10.0, read=15.0, write=10.0)

# Disable TLS warnings (not recommended for production)
os.environ['PYTHONWARNINGS'] = 'ignore:Unverified HTTPS request'

chrome_extension = {
    'id': 'fpdkjdnhkakefebpekbdhillbhonfjjp',
    'version': '1.0.7'
}
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'

warnings.simplefilter('ignore', InsecureRequestWarning)

def keep_alive(user, proxy):
    url = "https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive"
    headers = {
        "origin": f"chrome-extension://{chrome_extension['id']}",
        "authorization": f"Bearer {user['token']}",
        "content-type": "application/json",
        "user-agent": user_agent
    }
    body = {
        "username": user['email'],
        "extensionid": chrome_extension['id'],
        "numberoftabs": 0,
        "_v": chrome_extension['version']
    }
    
    try:
        with httpx.Client(proxies=proxy, verify=False, timeout=timeout) as client:
            client.post(url, headers=headers, json=body)
    except Exception as err:
        print(f"keepAlive request failed for {user['email']} and proxy {proxy}: {err}")
        raise err

def get_balance(user, proxy):
    url = "https://www.aeropres.in/api/atom/v1/userreferral/getpoint"
    headers = {
        "origin": f"chrome-extension://{chrome_extension['id']}",
        "authorization": f"Bearer {user['token']}",
        "content-type": "application/json",
        "user-agent": user_agent
    }

    try:
        with httpx.Client(proxies=proxy, verify=False, timeout=timeout) as client:
            response = client.get(url, headers=headers)
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
        #print(f"Cannot get balance for {user['email']}")
        raise err

def get_ip(proxy):
    proxy = {
        'http': proxy['http://'],
        'https': proxy['http://']
    }
    try:
        response = requests.get('https://api.ipify.org?format=json', proxies=proxy, verify=False)
        return response.json()['ip']
    except Exception as err:
        print(f"Can't get IP for proxy {proxy}")
        raise err

def with_retry(name, code, retries=0):
    if retries < 5:
        try:
            result = code()
            #if retries > 0:
            #    print(f"Successfully got results for {name} after {retries} retries")
            return result
        except:
            time.sleep(0.5)
            print(f"Retrying {retries} ({name})...")
            return with_retry(name, code, retries = retries + 1)
    else:
        print(f"Reached max retries for {name}")
        return None

def find_key_by_value(my_dict, target_value):
    for key, value in my_dict.items():
        if value == target_value:
            return key
    return None  # Return None if the value is not found

def find_available_proxy(user_id, proxies, print_ip = False):
    acquired = find_proxy_lock.acquire()

    if acquired:
        try:
            #print(f"Used proxies: {len(used_proxies)} of {len(proxies)}")
            proxy_url = find_key_by_value(used_proxies, user_id)
            next_proxy = proxy_url or next((p for p in proxies if p['http://'] not in used_proxies), None)

            if next_proxy:
                proxy = next_proxy
                ip = with_retry('getIP', lambda: get_ip(proxy))
                if ip is not None:
                    used_proxies[next_proxy['http://']] = user_id
                    if print_ip:
                        print(f'user {user_id} got {ip}')
                    return proxy
                else:
                    print(f'No IP for {user_id}. Next loop')
                    used_proxies[next_proxy] = None
                    find_proxy_lock.release()
                    return find_available_proxy(user_id, proxies)
            else:
                print("No available proxies")
                return None
        finally:
            try:
                find_proxy_lock.release()
            except Exception as err:
                pass
        

def farm(user, proxies, print_ip):
    proxy = find_available_proxy(user['email'], proxies, print_ip)
    if proxy:
        user_ip = get_ip(proxy)
        with_retry('keepAlive', lambda: keep_alive(user, proxy))
        points = with_retry('getBalance', lambda: get_balance(user, proxy)) or -1
        print(f"{user['email']:<40} | {points:.2f} | {format_date():<15} {' | IP: ' + user_ip}")
        if points == -1:
            used_proxies[proxy['http://']] = None
            farm(user, proxies, print_ip = True)
        else:
            if EXPORT_DATA: 
                save_to_sheet(user['email'], points, user_ip)
        
    else:
        print(f"Can't find a proxy for {user['email']}")
        cleaned_up = cleanup_proxies()
        print(f"Cleaned up {cleaned_up} proxies")
        if cleaned_up > 0:
            farm(user, proxies, print_ip)
    

def cleanup_proxies():
    before_clean_up = len(used_proxies)
    for proxy, user_id in list(used_proxies.items()):
        if user_id is None:
            del used_proxies[proxy]
    after_clean_up = len(used_proxies)
    return before_clean_up - after_clean_up

def format_date():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def reserve_proxies(users, proxies): 
    start_time = time.time()
    for user in users:
        find_available_proxy(user['email'], proxies, print_ip = True)

    print(f"\nIt took: {((time.time()  - start_time) / 60):.2f} minutes to find proxies {len(users)} users\n") 

# Main farming loop
def farm_for_all(users, proxies, nThreads, print_ip):
    start_time = time.time()
    batch_size = nThreads
    threads = []
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        for user in batch:
            thread = threading.Thread(target=farm, args=(user, proxies, print_ip))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    print(f"\nIt took: {((time.time()  - start_time) / 60):.2f} minutes to farm points for {len(users)} users\n")
    print('Sleep for 1 minute before next loop...')


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

    # 1st time need to allocate proxies in correct order, sequantually. 
    #farm_for_all(users, proxies, nThreads = 1, print_ip = True, export_sheet = export_sheet, user_group = user_group)
    reserve_proxies(users, proxies)

    farm_for_all(users, proxies, MAX_THREADS, False)

    schedule.every(2).minutes.do(farm_for_all, users, proxies, MAX_THREADS, False)

    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

used_proxies = {}