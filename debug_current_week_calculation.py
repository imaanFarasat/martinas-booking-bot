#!/usr/bin/env python3
"""
Debug the current week calculation to see why the bot can't find the data
"""

import sys
import os
from datetime import datetime, timedelta
import pytz

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DAYS_OF_WEEK

def debug_current_week_calculation():
    """Debug what the bot thinks the current week is"""
    print("🔍 DEBUGGING CURRENT WEEK CALCULATION")
    print("=" * 60)
    
    # Current date in Toronto timezone
    toronto_tz = pytz.timezone('America/Toronto')
    today = datetime.now(toronto_tz).date()
    print(f"📅 Today (Toronto time): {today} ({today.strftime('%A')})")
    
    # Calculate current week using the bot's logic
    days_since_sunday = (today.weekday() + 1) % 7
    current_week_start = today - timedelta(days=days_since_sunday)
    if today.weekday() == 6:  # Sunday
        current_week_start = today
    
    current_week_end = current_week_start + timedelta(days=6)
    
    print(f"\n📅 Bot's current week calculation:")
    print(f"   Week starts: {current_week_start} ({current_week_start.strftime('%A')})")
    print(f"   Week ends: {current_week_end} ({current_week_end.strftime('%A')})")
    
    # Show the week breakdown
    print(f"\n📊 Bot's week breakdown:")
    for i, day in enumerate(DAYS_OF_WEEK):
        date = current_week_start + timedelta(days=i)
        if date == today:
            print(f"   {i+1}. {day}: {date} ← TODAY")
        else:
            print(f"   {i+1}. {day}: {date}")
    
    # Show what data we actually have
    print(f"\n📊 ACTUAL DATA WE HAVE:")
    print(f"   Data week: September 14-20, 2025")
    print(f"   Data start: 2025-09-14 (Sunday)")
    print(f"   Data end: 2025-09-20 (Saturday)")
    
    # Compare
    data_start = datetime(2025, 9, 14).date()
    data_end = datetime(2025, 9, 20).date()
    
    print(f"\n🔍 COMPARISON:")
    print(f"   Bot thinks current week: {current_week_start} to {current_week_end}")
    print(f"   Data is for week: {data_start} to {data_end}")
    
    if current_week_start == data_start and current_week_end == data_end:
        print(f"   ✅ PERFECT MATCH! Bot should find the data")
    else:
        print(f"   ❌ MISMATCH! Bot won't find the data")
        print(f"   📅 Bot is looking for: {current_week_start} to {current_week_end}")
        print(f"   📅 Data exists for: {data_start} to {data_end}")
        
        # Calculate the difference
        days_diff = (current_week_start - data_start).days
        print(f"   📊 Difference: {days_diff} days")
        
        if days_diff > 0:
            print(f"   📅 Bot is looking {days_diff} days in the future")
        elif days_diff < 0:
            print(f"   📅 Bot is looking {abs(days_diff)} days in the past")
    
    # Show what the bot should be looking for
    print(f"\n💡 SOLUTION:")
    if current_week_start != data_start:
        print(f"   The bot needs to look for data in the week: {data_start} to {data_end}")
        print(f"   But it's currently looking for: {current_week_start} to {current_week_end}")
        print(f"   This is why it shows 'No Current Week Found'")

if __name__ == "__main__":
    debug_current_week_calculation()
