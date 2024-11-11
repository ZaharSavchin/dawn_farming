import asyncio

from core.auth import process_users
from core.farm import start_farming
from data.config import FARM_ONLY, VERIFY_ONLY
from core.verify import verify_users


if __name__ == '__main__':
    try:
        if VERIFY_ONLY:
            print('Starting verification only')
            verify_users()
        else:
            if FARM_ONLY == False:
                print('Starting authentification')
                process_users()
            else:
                print('Starting farm')
                asyncio.run(start_farming())
    except (KeyboardInterrupt, SystemExit):
        print("Program terminated by user.")