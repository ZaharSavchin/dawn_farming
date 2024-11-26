##########################################################################
# Script configuration #
##########################################################################

FARM_ONLY = False # Set True if you want only farm points
REGISTER = False # False = Login only | True = Register, then login
BOOST_USERS = False # Set True if you want to boost users
VERIFY_ONLY = False # True = Verify only | False = Register or farm

##########################################################################
# Variables configuration #
##########################################################################

API_KEY = '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' # ChatGpt API_KEY
MAX_RETRIES = 5 # Amount of retries in loop (login, register, farm) 
RETRY_DELAY = 3 # Delay betwwen requests (login, register only)
MAX_THREADS = 15  # Max amount of users processed in one moment (login, register only)
REF_CODE = 'REF_CODE' # Referal code for registration
GET_POINTS_RARELY = True # True = get balance called in 100 iteractions | False = called in 10 iteractions
MIN_SLEEP_TIME = 180 # Min and Max interval between ping requests
MAX_SLEEP_TIME = 420 # Min and Max interval between ping requests

##########################################################################
# Google export configuration #
##########################################################################

EXPORT_DATA = False # True if want to export | False if not
SHEET_ID = '18ieXul0QrwYlXcbpe-V3lF9DZs4hyKsuXvUYcwzexPk' # Your Google Sheet ID
LIST_NAME = 'Dawn' # Your Google Sheet List name
