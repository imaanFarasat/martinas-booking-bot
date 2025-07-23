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

def start_admin_bot():
    """Start the admin bot in a separate thread"""
    from main_start import start_admin_bot
    start_admin_bot()

def start_staff_bot():
    """Start the staff bot in a separate thread"""
    try:
        import asyncio
        import nest_asyncio
        
        # Enable nested event loops
        nest_asyncio.apply()
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        staff_bot = StaffBot()
        staff_bot.run()
    except Exception as e:
        print(f"Error starting staff bot: {e}")

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