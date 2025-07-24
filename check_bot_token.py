#!/usr/bin/env python3
"""
Check if bot token is being read correctly
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Checking bot token from .env file:")
print("=" * 40)

bot_token = os.getenv('BOT_TOKEN', 'NOT_FOUND')
admin_ids = os.getenv('ADMIN_IDS', 'NOT_FOUND')

print(f"BOT_TOKEN: {bot_token}")
print(f"ADMIN_IDS: {admin_ids}")

if bot_token == 'NOT_FOUND':
    print("❌ BOT_TOKEN not found in .env file")
elif bot_token == 'your_telegram_bot_token_here':
    print("❌ BOT_TOKEN still has placeholder value")
elif len(bot_token) < 10:
    print("❌ BOT_TOKEN seems too short")
else:
    print("✅ BOT_TOKEN looks valid")

print("=" * 40)
print("Make sure your .env file has the correct bot token!") 