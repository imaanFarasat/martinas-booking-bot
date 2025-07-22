#!/usr/bin/env python3
"""
Separate start script for main bot only
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get main bot token directly from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
    logger.error("❌ BOT_TOKEN not set or invalid")
    sys.exit(1)

logger.info(f"Starting main bot with token: {BOT_TOKEN[:10]}...")

# Import main bot directly
try:
    from bot_async import StaffSchedulerBot
    bot = StaffSchedulerBot()
    logger.info("Main bot created successfully")
    bot.run()
except Exception as e:
    logger.error(f"Error starting main bot: {e}")
    sys.exit(1) 