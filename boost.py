import sys
from core.boost import boost_user
from core.utils import load_file_lines
from farm.data import read_proxies, read_users
def main():
  already_boosted = load_file_lines('data/boosted.txt')
  sub_folder = sys.argv[1] if len(sys.argv) > 1 else None
  users = read_users(sub_folder)
  proxies = read_proxies(sub_folder)
  
  for i, user in enumerate(users):
    if user['email'] not in already_boosted:
       user = users[i]
       proxy = proxies[i]
       boost_user(user, proxy)
  
  print(f"All {len(users)} users boosted")
if __name__ == "__main__":
    main()    
