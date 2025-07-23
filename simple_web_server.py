#!/usr/bin/env python3
"""
Simplified web server that runs bots sequentially to avoid threading issues
"""
from flask import Flask
import os
import subprocess
import threading
import time

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

def run_bot_script(script_name, bot_name):
    """Run a bot script in a separate process"""
    try:
        print(f"Starting {bot_name}...")
        # Run the bot script as a separate process
        process = subprocess.Popen(
            ['python', script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"{bot_name} started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Error starting {bot_name}: {e}")
        return None

if __name__ == "__main__":
    # Start bots as separate processes instead of threads
    print("Starting bots as separate processes...")
    
    # Start admin bot
    admin_process = run_bot_script('main_start.py', 'Admin Bot')
    
    # Start staff bot
    staff_process = run_bot_script('staff_bot.py', 'Staff Bot')
    
    # Start the web server
    print("Starting Flask web server...")
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port) 