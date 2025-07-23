import os
from dotenv import load_dotenv

load_dotenv()

# Staff Bot Configuration
# 
# To set up the staff bot:
# 1. Create a new bot with @BotFather on Telegram
# 2. Get the token for your new bot
# 3. Set the STAFF_BOT_TOKEN environment variable
# 4. Run this bot separately from your main scheduling bot

# Staff Bot Token (from environment variable)
STAFF_BOT_TOKEN = os.getenv('STAFF_BOT_TOKEN', 'YOUR_STAFF_BOT_TOKEN_HERE')

# Instructions for setting up the staff bot:
"""
1. Go to @BotFather on Telegram
2. Send /newbot
3. Choose a name for your staff bot (e.g., "My Company Staff Schedule")
4. Choose a username (e.g., "mystaffschedule_bot")
5. Copy the token provided
6. Set the STAFF_BOT_TOKEN environment variable
7. Run the staff bot: python staff_bot.py

The staff bot will allow staff members to:
- Select their name from the list
- View their current week's schedule as text
- View their schedule history as text
- Switch between different staff members

Features:
✅ Individual staff access
✅ Current week schedule view (text format)
✅ Historical schedule browsing (text format)
✅ Easy staff switching
✅ Date display for each day
✅ Working hours and off days clearly shown
✅ No PDF generation - clean text display only
""" 