from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
import pytz


if not os.path.exists('logs'):
    os.mkdir('logs')

# Define a custom formatter that includes Pakistan Standard Time
class PKTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, pytz.timezone('Asia/Karachi'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')

# Create a RotatingFileHandler
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240)
file_handler.setFormatter(PKTFormatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)

# Configure the root logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)