from farm.dawn import chrome_extension, user_agent, timeout
import httpx
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
    try:
       with httpx.Client(proxies=proxy, verify=False, timeout=timeout) as client:
           client.post(url, headers=headers, json=body)
       successful_boosts += 1    
    except Exception as err:
       print(f"boost {boost} request failed for {email} and proxy {proxy}: {err}")
       continue
    
   if successful_boosts == len(boosts) :
     save_boosted_user(email) 
     print(f"User {email} boosted")  
   else:
     save_not_boosted_user(user, proxy) 
   
def save_boosted_user(email):
    save_to_file(email, 'data/boosted.txt')
def save_not_boosted_user(user, proxy):
    save_to_file(f"{user["email"]}:{user["token"]}", 'data/not_boosted/users.csv')
    save_to_file(proxy, 'data/not_boosted/proxies.txt')
def save_to_file(line, file):
    with open(file, 'a', encoding='utf-8') as f:
        f.write(f"{line}\n")    
