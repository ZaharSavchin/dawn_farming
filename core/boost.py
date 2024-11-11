from core.dawn import chrome_extension, user_agent, timeout
import requests

boosts = [
    {"twitter_x_id":"twitter_x_id"},
    {"telegramid": "telegramid"},
    {"discordid": "discordid"}
]

def boost_user(user, proxy):
    url = "https://www.aeropres.in/chromeapi/dawn/v1/profile/update?appid=66f7d995f30f347de44f6612"
    headers = {
        "origin": f"chrome-extension://{chrome_extension['id']}",
        "authorization": f"Bearer {user['token']}",
        "content-type": "application/json",
        "user-agent": user_agent
    }
    email = user["email"]
    successful_boosts = 0
    for boost in boosts:
        body = boost
        print(f'Boosting {email} in {boost}')
        try:
            requests.post(url, headers=headers, json=body, proxies=proxy, verify=False)
            successful_boosts += 1    
        except Exception as err:
            print(f"boost {boost} request failed for {email} and proxy {proxy}: {err}")
            continue
    if successful_boosts == len(boosts) :
        save_boosted_user(email) 
        print(f"User {email} boosted")  
    else:
        save_not_boosted_user(boost, email, proxy)

def save_boosted_user(email):
    with open('data/boosted.txt', 'a', encoding='utf-8') as f:
        f.write(f"{email}\n")

def save_not_boosted_user(boost, email, proxy):
    with open('data/not-boosted.txt', 'a', encoding='utf-8') as f:
        f.write(f"{boost} | {email}:{proxy}\n")
