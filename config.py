import os
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv
from notifier import TelegramErrorHandler

# Load environment variables
load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")
DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("API_KEY")

# Timezone setup
KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')

EMAIL_IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER")
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
BANK_EMAIL_SENDER = os.getenv("BANK_EMAIL_SENDER")


class KLFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=KL_TZ)
        return dt.timetuple()

# Logger setup
def get_logger():
    logger = logging.getLogger("finance_app")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = KLFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S MYT')
        
        # Console handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # Telegram handler (ERROR level and above)
        tg_handler = TelegramErrorHandler()
        tg_handler.setLevel(logging.ERROR)
        tg_handler.setFormatter(formatter)
        logger.addHandler(tg_handler)
    return logger

# This line is what app.py imports
logger = get_logger()