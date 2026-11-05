import os
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")
DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("API_KEY")

# Timezone setup
KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')

class KLFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=KL_TZ)
        return dt.timetuple()

# Logger setup
def get_logger():
    logger = logging.getLogger("finance_app")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = KLFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S MYT')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = get_logger()