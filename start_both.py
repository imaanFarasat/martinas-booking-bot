#!/usr/bin/env python3
"""
Start script that runs both the web server and the bot
"""
import os
import subprocess
import sys
import time

def main():
    """Main function to start both services"""
    print("Starting Booking Nail Admin Bot...")
    
    # Start the bot in a subprocess
    bot_process = subprocess.Popen([sys.executable, "main_start.py"])
    
    # Wait a moment for bot to start
    time.sleep(2)
    
    # Start the web server
    print("Starting web server...")
    web_process = subprocess.Popen([sys.executable, "web_server.py"])
    
    try:
        # Keep both processes running
        bot_process.wait()
        web_process.wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        bot_process.terminate()
        web_process.terminate()

if __name__ == "__main__":
    main() 