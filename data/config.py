API_KEY = 'API_KEY' # ChatGpt API_KEY
MAX_RETRIES = 5 # Кол-во повторных попыток регистрации или логина
RETRY_DELAY = 3 # Пауза между запросами в секундах
REGISTER = False # False = Login only | True = Register, then login
MAX_THREADS = 10  # Укажите количество потоков
FARM_ONLY = True # Set True if you want only farm points
REF_CODE = 'REF_CODE' # Referal code for registration
BOOST_USERS = False # Set True if you want to boost users
VERIFY_ONLY = False # True = Verify only | False = Register or farm

##########################################################################
# Google export configuration #
##########################################################################

EXPORT_DATA = False # True if want to export | False if not
SHEET_ID = 'SHEET_ID' # Your Google Sheet ID
LIST_NAME = 'LIST_NAME' # Your Google Sheet List name
