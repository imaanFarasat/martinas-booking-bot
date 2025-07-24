#!/usr/bin/env python3
"""
Main entry point for the Staff Scheduler Bot
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from bot_async import StaffSchedulerBot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to run the bot"""
    try:
        # Check if BOT_TOKEN is set
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
            logger.error("❌ BOT_TOKEN not set or invalid")
            logger.info("💡 Please set BOT_TOKEN in your environment variables")
            return
        
        logger.info(f"Starting main bot with token: {bot_token[:10]}...")
        
        # Create and run bot
        bot = StaffSchedulerBot()
        logger.info("Main bot created successfully")
        
        # Run the bot
        await bot.run_async()
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Get port from environment (for Railway)
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Starting bot on port {port}")
    
    # Run the bot
    asyncio.run(main()) 