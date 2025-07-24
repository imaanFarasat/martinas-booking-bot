#!/usr/bin/env python3
"""
Staff Scheduler Bot - Production-ready startup script with Railway health checks
"""

import os
import sys
import asyncio
import logging
import threading
import time
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify
from bot_async import StaffSchedulerBot
from database_factory import get_database_manager

# Load environment variables
load_dotenv()

# Global flag to control the Flask server
flask_app_running = False

# Create Flask app for Railway health checks
app = Flask(__name__)

@app.route('/')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        "status": "healthy",
        "service": "Staff Scheduler Bot v2.0",
        "timestamp": time.time(),
        "features": ["bulk_scheduling", "webhooks", "connection_pooling", "templates"]
    })

@app.route('/health')
def detailed_health():
    """Detailed health check"""
    try:
        # Test database connection
        db = get_database_manager()
        staff_count = len(db.get_all_staff())
        
        return jsonify({
            "status": "healthy",
            "service": "Staff Scheduler Bot v2.0",
            "database": "connected",
            "staff_count": staff_count,
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "Staff Scheduler Bot v2.0",
            "database": "error",
            "error": str(e),
            "timestamp": time.time()
        }), 500

def setup_logging():
    """Configure production logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log') if os.getenv('LOG_FILE') else logging.NullHandler()
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('mysql.connector').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Flask logs

def check_environment():
    """Validate environment configuration"""
    logger = logging.getLogger(__name__)
    
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
        logger.error("❌ BOT_TOKEN not set or invalid")
        return False
    
    logger.info(f"✅ Bot configured: {bot_token[:10]}...")
    
    if os.getenv('WEBHOOK_URL'):
        logger.info(f"🌐 Production mode - Webhook enabled")
    else:
        logger.info("🔧 Development mode - Polling")
    
    return True

def cleanup_duplicate_records():
    """One-time cleanup of duplicate schedule records"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🧹 Checking for duplicate schedule records...")
        
        db = get_database_manager()
        
        # Only run cleanup for MySQL databases (production)
        if not hasattr(db, 'get_connection'):
            logger.info("📍 SQLite database detected - no cleanup needed")
            return
        
        logger.info("🚨 MySQL database detected - running duplicate cleanup...")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get all staff
        cursor.execute("SELECT id, name FROM staff ORDER BY name")
        staff_list = cursor.fetchall()
        
        total_cleaned = 0
        
        for staff_id, staff_name in staff_list:
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            for day in days:
                # Get all records for this staff/day - ORDER BY updated_at DESC
                cursor.execute('''
                    SELECT id, schedule_date, is_working, start_time, end_time, updated_at
                    FROM schedules 
                    WHERE staff_id = %s AND day_of_week = %s
                    ORDER BY updated_at DESC
                ''', (staff_id, day))
                
                records = cursor.fetchall()
                
                if len(records) > 1:
                    logger.info(f"🔍 Found {len(records)} duplicate records for {staff_name} {day}")
                    
                    # Keep the most recent record, delete the rest
                    keep_record = records[0]
                    delete_records = records[1:]
                    
                    for record in delete_records:
                        cursor.execute('DELETE FROM schedules WHERE id = %s', (record[0],))
                        total_cleaned += 1
                    
                    conn.commit()
        
        cursor.close()
        conn.close()
        
        if total_cleaned > 0:
            logger.info(f"✅ Cleanup completed! Removed {total_cleaned} duplicate records.")
        else:
            logger.info("✅ No duplicate records found - database is clean.")
            
    except Exception as e:
        logger.error(f"❌ Error during duplicate cleanup: {e}")
        # Don't fail startup due to cleanup issues
        pass

def run_health_server():
    """Run Flask health check server for Railway in background"""
    global flask_app_running
    try:
        port = int(os.getenv('PORT', 8000))
        logger = logging.getLogger(__name__)
        logger.info(f"🌐 Starting health check server on port {port}")
        flask_app_running = True
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Health server error: {e}")
    finally:
        flask_app_running = False

async def start_bot():
    """Start the bot with error handling"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🤖 Initializing Staff Scheduler Bot...")
        bot = StaffSchedulerBot()
        
        logger.info("🚀 Starting bot...")
        await bot.run_async()
        
        return True
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
        return True
    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
        logger.error("Traceback:", exc_info=True)
        return False

def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🤖 STAFF SCHEDULER BOT v2.0 STARTUP")
    
    if not check_environment():
        logger.error("❌ Environment check failed")
        sys.exit(1)
    
    # ONE-TIME: Clean up duplicate records
    cleanup_duplicate_records()
    
    # Start health check server in background thread (for Railway monitoring)
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    logger.info("🌐 Health check server started in background thread")
    
    # Run bot in main thread (required for asyncio signal handling)
    try:
        success = asyncio.run(start_bot())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"💥 Unhandled exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 