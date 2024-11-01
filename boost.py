import sys
from core.boost import boost_user
from core.utils import load_file_lines
from core.proxies import fetch_proxies
from core.utils import read_tokens


def main():
  already_boosted = load_file_lines('data/boosted.txt')

  users = read_tokens()
  proxies = fetch_proxies()
  
  for i, user in enumerate(users):
    if user['email'] not in already_boosted:
       user = users[i]
       proxy = proxies[i]
       boost_user(user, proxy)
  
  print(f"All {len(users)} users boosted")
if __name__ == "__main__":
    main()    