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

# Database - Use environment variable for shared database on Render
DATABASE_PATH = os.getenv('DATABASE_PATH', 'staff_scheduler.db')

# PDF Settings
PDF_FILENAME = 'weekly_schedule.pdf'
PDF_TITLE = 'Weekly Staff Schedule' 