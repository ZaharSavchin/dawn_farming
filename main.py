from core.auth import process_users
from core.farm import farm_points
from data.config import FARM_ONLY


if __name__ == '__main__':
    if FARM_ONLY == False:
        process_users()
    else:
        farm_points()