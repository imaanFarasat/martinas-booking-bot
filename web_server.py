#!/usr/bin/env python3
"""
Simple web server to keep the bot running on Render
"""
import os
import threading
import time
from flask import Flask, render_template_string

app = Flask(__name__)

# HTML template for the status page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Booking Nail Admin Bot</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status { color: #28a745; font-weight: bold; }
        .bot-info { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Booking Nail Admin Bot</h1>
        <div class="bot-info">
            <p><span class="status">✅ Status: Running</span></p>
            <p><strong>Bot Type:</strong> Admin/Management Bot</p>
            <p><strong>Function:</strong> Staff scheduling and management</p>
            <p><strong>Last Updated:</strong> {{ last_updated }}</p>
        </div>
        <p>This bot is running in the background and handling Telegram messages.</p>
        <p>To use the bot, go to your Telegram and start a conversation with the bot.</p>
    </div>
</body>
</html>
"""

def run_bot():
    """Run the bot in a separate thread"""
    try:
        # Import and run the main bot
        import main_start
        print("Bot started successfully in background thread")
    except Exception as e:
        print(f"Bot error: {e}")

@app.route('/')
def home():
    """Home page showing bot status"""
    return render_template_string(HTML_TEMPLATE, last_updated=time.strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "healthy", "bot": "running"}

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 10000))
    
    print(f"Starting web server on port {port}")
    print("Bot is running in background thread")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False) 