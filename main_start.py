#!/usr/bin/env python3
"""
Main entry point for the Staff Scheduler Bot
"""
import os
import asyncio
import logging
import threading
from dotenv import load_dotenv
from flask import Flask, jsonify
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app for health checks
app = Flask(__name__)

@app.route('/')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        "status": "healthy",
        "service": "Staff Scheduler Bot",
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    """Detailed health check"""
    return jsonify({
        "status": "healthy",
        "service": "Staff Scheduler Bot",
        "database": "MySQL",
        "timestamp": time.time()
    })

def run_web_server():
    """Run the Flask web server"""
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🌐 Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

async def start_bot():
    """Start the bot in background"""
    try:
        from bot_async import StaffSchedulerBot
        
        # Check if BOT_TOKEN is set
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
            logger.error("❌ BOT_TOKEN not set or invalid")
            return
        
        logger.info(f"🤖 Starting bot with token: {bot_token[:10]}...")
        
        # Create and run bot
        bot = StaffSchedulerBot()
        logger.info("✅ Bot created successfully")
        
        # Run the bot
        await bot.run_async()
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()

def run_bot_in_background():
    """Run bot in background thread"""
    try:
        asyncio.run(start_bot())
    except Exception as e:
        logger.error(f"❌ Bot thread error: {e}")

if __name__ == "__main__":
    # Debug environment variables
    logger.info("🔍 Checking environment variables...")
    mysql_host = os.getenv('MYSQL_HOST', 'NOT_SET')
    mysql_user = os.getenv('MYSQL_USER', 'NOT_SET')
    mysql_database = os.getenv('MYSQL_DATABASE', 'NOT_SET')
    bot_token = os.getenv('BOT_TOKEN', 'NOT_SET')
    
    # Check Railway specific variables
    railway_mysql_host = os.getenv('RAILWAY_MYSQL_HOST', 'NOT_SET')
    railway_mysql_user = os.getenv('RAILWAY_MYSQL_USER', 'NOT_SET')
    railway_mysql_database = os.getenv('RAILWAY_MYSQL_DATABASE', 'NOT_SET')
    
    logger.info(f"MySQL Host: {mysql_host}")
    logger.info(f"MySQL User: {mysql_user}")
    logger.info(f"MySQL Database: {mysql_database}")
    logger.info(f"Railway MySQL Host: {railway_mysql_host}")
    logger.info(f"Railway MySQL User: {railway_mysql_user}")
    logger.info(f"Railway MySQL Database: {railway_mysql_database}")
    logger.info(f"Bot Token: {bot_token[:10] if bot_token != 'NOT_SET' else 'NOT_SET'}...")
    
    # Get port from environment (for Railway)
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Starting application on port {port}")
    
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot_in_background, daemon=True)
    bot_thread.start()
    logger.info("🤖 Bot started in background")
    
    # Run web server (this will block and handle requests)
    run_web_server() 