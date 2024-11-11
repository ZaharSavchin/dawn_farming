import asyncio

from core.auth import process_users
from core.dawn import start_farming
from data.config import FARM_ONLY


if __name__ == '__main__':
    try:
        if FARM_ONLY == False:
            process_users()
        else:
            asyncio.run(start_farming())
    except (KeyboardInterrupt, SystemExit):
        print("Program terminated by user.")