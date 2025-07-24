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

# Load environment variables
load_dotenv()

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
    return jsonify({
        "status": "healthy",
        "service": "Staff Scheduler Bot v2.0",
        "database": "MySQL with Connection Pool",
        "deployment": "Production Ready",
        "timestamp": time.time()
    })

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

def run_health_server():
    """Run Flask health check server for Railway"""
    port = int(os.getenv('PORT', 8000))
    logger = logging.getLogger(__name__)
    logger.info(f"🌐 Starting health check server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def start_bot():
    """Start the bot with error handling"""
    logger = logging.getLogger(__name__)
    
    try:
        from bot_async import StaffSchedulerBot
        
        logger.info("🤖 Creating bot instance...")
        bot = StaffSchedulerBot()
        
        logger.info("🚀 Starting Staff Scheduler Bot v2.0")
        logger.info(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await bot.run_async()
        return True
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
        return True
    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return False

def run_bot_in_background():
    """Run bot in background thread"""
    try:
        asyncio.run(start_bot())
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Bot thread error: {e}")

def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🤖 STAFF SCHEDULER BOT v2.0 STARTUP")
    
    if not check_environment():
        logger.error("❌ Environment check failed")
        sys.exit(1)
    
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot_in_background, daemon=True)
    bot_thread.start()
    logger.info("🤖 Bot started in background thread")
    
    # Run health check server (this blocks and handles Railway health checks)
    try:
        run_health_server()
    except Exception as e:
        logger.error(f"💥 Health server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 