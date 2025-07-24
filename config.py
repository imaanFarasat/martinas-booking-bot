import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Admin Configuration
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = []
if ADMIN_IDS_STR:
    # Parse comma-separated admin IDs
    for admin_id in ADMIN_IDS_STR.split(','):
        try:
            ADMIN_IDS.append(int(admin_id.strip()))
        except ValueError:
            print(f"Warning: Invalid admin ID '{admin_id}'")

# Time Constraints
MIN_START_TIME = "09:45"
MAX_END_TIME = "21:00"

# Days of the week
DAYS_OF_WEEK = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

# Database Configuration
# Priority: MySQL > PostgreSQL > SQLite
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'staff_scheduler')
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL connection string (fallback)
DATABASE_PATH = os.getenv('DATABASE_PATH', 'shared_scheduler.db')  # SQLite fallback

# Database type selection
USE_MYSQL = bool(MYSQL_HOST and MYSQL_USER and MYSQL_DATABASE)
USE_POSTGRESQL = bool(DATABASE_URL) and not USE_MYSQL
USE_SQLITE = not (USE_MYSQL or USE_POSTGRESQL)

# PDF Settings
PDF_FILENAME = 'weekly_schedule.pdf'
PDF_TITLE = 'Weekly Staff Schedule' 