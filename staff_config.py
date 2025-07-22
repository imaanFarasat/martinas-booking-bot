import os
from dotenv import load_dotenv

load_dotenv()

# Database - Use environment variable for shared database on Render
DATABASE_PATH = os.getenv('DATABASE_PATH', 'staff_scheduler.db')

# Days of the week
DAYS_OF_WEEK = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] 