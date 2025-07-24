#!/usr/bin/env python3
"""
Staff Scheduler Bot - Production-ready startup script
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

async def start_bot():
    """Start the bot with error handling"""
    logger = logging.getLogger(__name__)
    
    try:
        from bot_async import StaffSchedulerBot
        
        logger.info("🤖 Creating bot instance...")
        bot = StaffSchedulerBot()
        
        logger.info("🚀 Starting Staff Scheduler Bot")
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

def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🤖 STAFF SCHEDULER BOT STARTUP")
    
    if not check_environment():
        logger.error("❌ Environment check failed")
        sys.exit(1)
    
    try:
        success = asyncio.run(start_bot())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"💥 Unhandled exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 