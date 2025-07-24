#!/usr/bin/env python3
"""
Debug Railway environment variables
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Railway Environment Variables Debug")
print("=" * 50)

# Check all relevant environment variables
env_vars = [
    'BOT_TOKEN',
    'ADMIN_IDS', 
    'MYSQL_HOST',
    'MYSQL_PORT',
    'MYSQL_USER',
    'MYSQL_PASSWORD',
    'MYSQL_DATABASE',
    'PORT'
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        if 'PASSWORD' in var or 'TOKEN' in var:
            print(f"✅ {var}: {'*' * len(value)} (length: {len(value)})")
        else:
            print(f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: Not set")

print("\n" + "=" * 50)
print("💡 If MySQL variables are not set, check Railway environment variables") 