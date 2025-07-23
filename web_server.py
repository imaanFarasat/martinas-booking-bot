from flask import Flask
import threading
import os
from main_start import start_admin_bot

app = Flask(__name__)

@app.route('/')
def home():
    return "Admin Bot is running! 🤖"

@app.route('/health')
def health():
    return "OK", 200

def start_bot():
    """Start the admin bot in a separate thread"""
    start_admin_bot()

if __name__ == "__main__":
    # Start the bot in a background thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start the web server
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port) 