API_KEY = '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' # ChatGpt API_KEY
MAX_RETRIES = 5 # Кол-во повторных попыток регистрации или логина
RETRY_DELAY = 3 # Пауза между запросами в секундах
REGISTER = False # False = Login only | True = Register, then login
MAX_THREADS = 15  # Укажите количество потоков
FARM_ONLY = True # Set True if you want only farm points
REF_CODE = 'REF_CODE' # Referal code for registration
BOOST_USERS = False # Set True if you want to boost users
VERIFY_ONLY = False # True = Verify only | False = Register or farm
GET_POINTS_RARELY = True # True = get balance called in 100 iteractions | False = called in 10 iteractions
MIN_SLEEP_TIME = 60 # Min and Max interval between ping requests
MAX_SLEEP_TIME = 180 # Min and Max interval between ping requests

##########################################################################
# Google export configuration #
##########################################################################

EXPORT_DATA = False # True if want to export | False if not
SHEET_ID = 'SHEET_ID' # Your Google Sheet ID
LIST_NAME = 'LIST_NAME' # Your Google Sheet List name
