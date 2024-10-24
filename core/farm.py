import sys
import asyncio

from export.sheets import ExportSheet
from core.proxies import fetch_proxies
from core.dawn import start_farming
from core.utils import read_tokens
# from data.config import 

def farm_points():
    
    nThreads = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    users = read_tokens()
    proxies = fetch_proxies()
    print(f"Configured {len(users)} accounts and {len(proxies)} proxies")

    #export_sheet = ExportSheet(
    #    spreadsheet_id = 'TBD',
    #    sheet = 'TBD'
    #)
    export_sheet = None

    asyncio.run(start_farming(users, proxies, nThreads, export_sheet)) 