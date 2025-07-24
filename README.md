# Staff Scheduler Bot

A Telegram bot for managing staff schedules with enhanced database logging and tracking.

## Features

- **Staff Management**: Add and remove staff members
- **Schedule Management**: Create and edit weekly schedules for staff
- **Database Logging**: All changes are tracked in the database for audit purposes
- **PDF Export**: Generate weekly schedule PDFs
- **Schedule History**: View historical schedules
- **Admin Only**: Secure access with admin user verification

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install MySQL** (if not already installed):
   - **Windows**: Download from [MySQL website](https://dev.mysql.com/downloads/mysql/)
   - **macOS**: `brew install mysql`
   - **Ubuntu/Debian**: `sudo apt install mysql-server`
   - **CentOS/RHEL**: `sudo yum install mysql-server`

2. **Environment Variables**:
   Create a `.env` file with:
   ```
   BOT_TOKEN=your_telegram_bot_token
   ADMIN_IDS=123456789,987654321
   
   # Database Configuration (choose one):
   # MySQL (recommended):
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=staff_scheduler
   
   # PostgreSQL (alternative):
   # DATABASE_URL=postgresql://user:password@localhost:5432/database
   
   # SQLite (fallback):
   # DATABASE_PATH=shared_scheduler.db
   ```

3. **Setup MySQL** (recommended):
   ```bash
   python setup_mysql.py
   ```

4. **Run the Bot**:
   ```bash
   python main_start.py
   ```

## Database Structure

The bot supports multiple database types with the following tables:

- **staff**: Staff member information
- **schedules**: Weekly schedule data
- **schedule_changes**: Audit log of all changes

### Database Priority:
1. **MySQL** (recommended for production)
2. **PostgreSQL** (alternative)
3. **SQLite** (fallback for development)

## Usage

1. Start the bot with `/start`
2. Add staff members through Staff Management
3. Set schedules for each staff member
4. Export PDF when all schedules are complete

## Database Logging

All actions are logged in the `schedule_changes` table:
- Staff additions/removals
- Schedule modifications
- User who made the change
- Timestamp of changes

This data can be used for:
- Audit trails
- Future staff bot integration
- Change tracking and reporting

## Files Structure

- `bot_async.py` - Main bot logic
- `database.py` - Database operations with logging
- `config.py` - Configuration settings
- `main_start.py` - Bot startup script
- `pdf_generator.py` - PDF generation
- `validators.py` - Input validation

## Future Enhancements

- Staff bot for viewing schedules (using the logged data)
- Web dashboard for schedule management
- Advanced reporting and analytics 