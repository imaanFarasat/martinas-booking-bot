#!/usr/bin/env python3
"""
Debug script to see what's in the .env file
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Debugging .env file values:")
print("=" * 40)

# Check all environment variables
env_vars = [
    'BOT_TOKEN',
    'ADMIN_IDS', 
    'MYSQL_HOST',
    'MYSQL_PORT',
    'MYSQL_USER',
    'MYSQL_PASSWORD',
    'MYSQL_DATABASE',
    'MIN_START_TIME',
    'MAX_END_TIME'
]

for var in env_vars:
    value = os.getenv(var, 'NOT_SET')
    if 'PASSWORD' in var:
        # Hide password but show length
        display_value = '*' * len(value) if value != 'NOT_SET' else 'NOT_SET'
        print(f"{var}: {display_value} (length: {len(value)})")
    else:
        print(f"{var}: {value}")

print("\n" + "=" * 40)
print("If MYSQL_PASSWORD shows length 0, the password is not being read correctly.") 