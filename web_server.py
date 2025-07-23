from flask import Flask
import threading
import os
from main_start import start_admin_bot
from staff_bot import StaffBot

app = Flask(__name__)

@app.route('/')
def home():
    return "Both Admin and Staff Bots are running! 🤖👥"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/test')
def test():
    """Test endpoint to check bot status"""
    import threading
    active_threads = threading.enumerate()
    bot_threads = [t for t in active_threads if 'bot' in t.name.lower()]
    
    return {
        "status": "running",
        "active_threads": len(active_threads),
        "bot_threads": len(bot_threads),
        "thread_names": [t.name for t in active_threads]
    }

def start_admin_bot():
    """Start the admin bot in a separate thread"""
    try:
        import asyncio
        import nest_asyncio
        import logging
        
        # Set up logging for this thread
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        logger.info("Starting admin bot thread...")
        
        # Enable nested event loops
        nest_asyncio.apply()
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from bot_async import StaffSchedulerBot
        bot = StaffSchedulerBot()
        logger.info("Admin bot created, starting polling...")
        
        # Run the bot in the event loop
        loop.run_until_complete(bot.run_async())
    except Exception as e:
        import traceback
        print(f"Error starting admin bot: {e}")
        traceback.print_exc()

def start_staff_bot():
    """Start the staff bot in a separate thread"""
    try:
        import asyncio
        import nest_asyncio
        import logging
        
        # Set up logging for this thread
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        logger.info("Starting staff bot thread...")
        
        # Enable nested event loops
        nest_asyncio.apply()
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        staff_bot = StaffBot()
        logger.info("Staff bot created, starting polling...")
        
        # Run the bot in the event loop
        loop.run_until_complete(staff_bot.run_async())
    except Exception as e:
        import traceback
        print(f"Error starting staff bot: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Start the admin bot in a background thread
    admin_bot_thread = threading.Thread(target=start_admin_bot, daemon=True)
    admin_bot_thread.start()
    
    # Start the staff bot in a background thread
    staff_bot_thread = threading.Thread(target=start_staff_bot, daemon=True)
    staff_bot_thread.start()
    
    # Start the web server
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port) 