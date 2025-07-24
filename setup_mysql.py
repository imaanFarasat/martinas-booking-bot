#!/usr/bin/env python3
"""
MySQL Setup Script for Staff Scheduler Bot
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def test_mysql_connection():
    """Test MySQL connection with current environment variables"""
    try:
        from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
        
        print("🔍 Testing MySQL connection...")
        print(f"Host: {MYSQL_HOST}")
        print(f"Port: {MYSQL_PORT}")
        print(f"User: {MYSQL_USER}")
        print(f"Database: {MYSQL_DATABASE}")
        
        # Test connection without database first
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        
        print("✅ Connected to MySQL server successfully!")
        
        # Test database creation
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        print(f"✅ Database '{MYSQL_DATABASE}' ready")
        
        # Test connection with database
        conn.close()
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        
        print("✅ Connected to database successfully!")
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def setup_mysql_environment():
    """Interactive setup for MySQL environment variables"""
    print("🚀 MySQL Setup for Staff Scheduler Bot")
    print("=" * 50)
    
    # Get MySQL configuration
    host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    port = input("MySQL Port (default: 3306): ").strip() or "3306"
    user = input("MySQL User (default: root): ").strip() or "root"
    password = input("MySQL Password: ").strip()
    database = input("Database Name (default: staff_scheduler): ").strip() or "staff_scheduler"
    
    # Create .env content
    env_content = f"""# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789,987654321

# MySQL Configuration
MYSQL_HOST={host}
MYSQL_PORT={port}
MYSQL_USER={user}
MYSQL_PASSWORD={password}
MYSQL_DATABASE={database}

# Time Constraints
MIN_START_TIME=09:45
MAX_END_TIME=21:00
"""
    
    # Write to .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(f"\n✅ Environment variables saved to .env file")
    print(f"📝 Please update BOT_TOKEN and ADMIN_IDS with your actual values")
    
    return True

def test_database_manager():
    """Test the database manager with MySQL"""
    try:
        print("\n🧪 Testing Database Manager...")
        from database_factory import get_database_manager
        
        db = get_database_manager()
        print(f"✅ Database manager created: {type(db).__name__}")
        
        # Test basic operations
        staff_count = len(db.get_all_staff())
        print(f"✅ Staff count: {staff_count}")
        
        # Test adding a test staff member
        test_staff_id = db.add_staff("Test Staff")
        if test_staff_id:
            print(f"✅ Test staff added with ID: {test_staff_id}")
            
            # Test schedule operations
            db.save_schedule(
                staff_id=test_staff_id,
                day_of_week="Monday",
                is_working=True,
                start_time="09:00",
                end_time="17:00",
                schedule_date="2024-01-01",
                changed_by="SETUP_TEST"
            )
            print("✅ Schedule saved successfully")
            
            # Test retrieving schedule changes
            changes = db.get_schedule_changes(limit=5)
            print(f"✅ Retrieved {len(changes)} recent changes")
            
            # Clean up test data
            db.remove_staff(test_staff_id)
            print("✅ Test data cleaned up")
        else:
            print("❌ Failed to add test staff")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database manager test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🗄️ MySQL Setup for Staff Scheduler Bot")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("📝 No .env file found. Let's create one...")
        setup_mysql_environment()
    
    # Test connection
    if not test_mysql_connection():
        print("\n❌ MySQL connection failed. Please check your configuration.")
        print("💡 Make sure MySQL is running and your credentials are correct.")
        return False
    
    # Test database manager
    if not test_database_manager():
        print("\n❌ Database manager test failed.")
        return False
    
    print("\n🎉 MySQL setup completed successfully!")
    print("🚀 You can now run the bot with: python main_start.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 