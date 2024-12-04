from dotenv import load_dotenv
from os import getenv

import pytz

load_dotenv(dotenv_path='.env')


TOKEN = getenv('BOT_TOKEN')

notifications = False

NOTIFICATION_SPREADSHEET_URL = getenv('NOTIFICATION_SPREADSHEET_URL')
TECHSUPPORT_SPREADSHEET_URL = getenv('TECHSUPPORT_SPREADSHEET_URL')
KEY_PATH = getenv('KEY_PATH')

TIMEZONE = pytz.timezone('Europe/Moscow')

API_PATH = getenv('API_PATH')

SENDING_TIME = {'DAY': '22:26', 'WEEK': '12:00', 'MONTH': '10:30'}

WORKING_DAYS = '0-4'  # 0-monday, 1-tuesday, etc...
WEEKLY_DAY = 'tue'
MONTHLY_DAY = '8'
