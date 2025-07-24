#!/usr/bin/env python3
"""
Main entry point for the Staff Scheduler Bot
"""
import os
import asyncio
import logging
import threading
from dotenv import load_dotenv
from bot_async import StaffSchedulerBot
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
    app.run(host='0.0.0.0', port=port, debug=False)

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
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    logger.info("🌐 Web server started for health checks")
    
    # Run the bot
    asyncio.run(main()) 