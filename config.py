import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Webhook Configuration (for production)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Set this in production (e.g., Railway)
PORT = int(os.getenv('PORT', 8000))

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

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.getenv('LOG_FILE')  # Optional: set to enable file logging

# Scheduling Configuration
MAX_BULK_OPERATIONS = int(os.getenv('MAX_BULK_OPERATIONS', 50))  # Prevent abuse
SESSION_TIMEOUT_HOURS = int(os.getenv('SESSION_TIMEOUT_HOURS', 24))  # Auto-cleanup old sessions
CONFLICT_WARNING_THRESHOLD = float(os.getenv('CONFLICT_WARNING_THRESHOLD', 0.5))  # 50% staff off = warning

# Database Configuration
# Priority: MySQL > PostgreSQL > SQLite
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'staff_scheduler')

# Railway specific: Check for Railway MySQL environment variables
if not MYSQL_HOST or MYSQL_HOST == 'localhost':
    # Try Railway's default MySQL environment variables
    RAILWAY_MYSQL_HOST = os.getenv('RAILWAY_MYSQL_HOST')
    RAILWAY_MYSQL_USER = os.getenv('RAILWAY_MYSQL_USER')
    RAILWAY_MYSQL_PASSWORD = os.getenv('RAILWAY_MYSQL_PASSWORD')
    RAILWAY_MYSQL_DATABASE = os.getenv('RAILWAY_MYSQL_DATABASE')
    
    if RAILWAY_MYSQL_HOST:
        MYSQL_HOST = RAILWAY_MYSQL_HOST
        MYSQL_USER = RAILWAY_MYSQL_USER or MYSQL_USER
        MYSQL_PASSWORD = RAILWAY_MYSQL_PASSWORD or MYSQL_PASSWORD
        MYSQL_DATABASE = RAILWAY_MYSQL_DATABASE or MYSQL_DATABASE

DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL connection string (fallback)
DATABASE_PATH = os.getenv('DATABASE_PATH', 'shared_scheduler.db')  # SQLite fallback

# Database type selection
USE_MYSQL = bool(MYSQL_HOST and MYSQL_USER and MYSQL_DATABASE and MYSQL_HOST != 'localhost')
USE_POSTGRESQL = bool(DATABASE_URL) and not USE_MYSQL
USE_SQLITE = not (USE_MYSQL or USE_POSTGRESQL)

# PDF Settings
PDF_FILENAME = 'weekly_schedule.pdf'
PDF_TITLE = 'Weekly Staff Schedule'

# Backup Configuration
BACKUP_ENABLED = os.getenv('BACKUP_ENABLED', 'false').lower() == 'true'
BACKUP_INTERVAL_HOURS = int(os.getenv('BACKUP_INTERVAL_HOURS', 24))
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', 7)) 