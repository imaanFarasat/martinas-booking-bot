#!/usr/bin/env python3
"""
Check what day is considered the first day of the week in the system
"""

import sys
import os
from datetime import datetime, timedelta
import pytz

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DAYS_OF_WEEK

def check_week_start():
    """Check what day is considered the first day of the week"""
    print("🔍 CHECKING WEEK START DAY")
    print("=" * 50)
    
    # Current date
    toronto_tz = pytz.timezone('America/Toronto')
    today = datetime.now(toronto_tz).date()
    print(f"📅 Today: {today} ({today.strftime('%A')})")
    
    # Show the DAYS_OF_WEEK configuration
    print(f"\n📋 DAYS_OF_WEEK configuration:")
    print(f"   {DAYS_OF_WEEK}")
    print(f"   First day: {DAYS_OF_WEEK[0]}")
    print(f"   Last day: {DAYS_OF_WEEK[-1]}")
    
    # Calculate current week using the system's logic
    days_since_sunday = (today.weekday() + 1) % 7
    current_week_start = today - timedelta(days=days_since_sunday)
    if today.weekday() == 6:  # Sunday
        current_week_start = today
    
    current_week_end = current_week_start + timedelta(days=6)
    
    print(f"\n📅 Current week calculation:")
    print(f"   Week starts: {current_week_start} ({current_week_start.strftime('%A')})")
    print(f"   Week ends: {current_week_end} ({current_week_end.strftime('%A')})")
    
    # Show the week breakdown
    print(f"\n📊 Week breakdown:")
    for i, day in enumerate(DAYS_OF_WEEK):
        date = current_week_start + timedelta(days=i)
        if date == today:
            print(f"   {i+1}. {day}: {date} ← TODAY")
        else:
            print(f"   {i+1}. {day}: {date}")
    
    # Show what the system considers as week boundaries
    print(f"\n🔍 System Logic:")
    print(f"   First day of week: {DAYS_OF_WEEK[0]} (Sunday)")
    print(f"   Last day of week: {DAYS_OF_WEEK[-1]} (Saturday)")
    print(f"   Week calculation: Sunday to Saturday")
    
    # Show the calculation step by step
    print(f"\n📊 Calculation breakdown:")
    print(f"   Today: {today} (weekday {today.weekday()})")
    print(f"   days_since_sunday = (today.weekday() + 1) % 7")
    print(f"   days_since_sunday = ({today.weekday()} + 1) % 7 = {days_since_sunday}")
    print(f"   week_start = today - {days_since_sunday} days = {current_week_start}")
    
    # Show what this means for September 14-20
    print(f"\n📅 For September 14-20, 2025:")
    sept_14 = datetime(2025, 9, 14).date()  # Sunday
    sept_20 = datetime(2025, 9, 20).date()  # Saturday
    
    print(f"   Week starts: {sept_14} ({sept_14.strftime('%A')})")
    print(f"   Week ends: {sept_20} ({sept_20.strftime('%A')})")
    
    # Show the week breakdown for September 14-20
    print(f"\n📊 September 14-20 breakdown:")
    for i, day in enumerate(DAYS_OF_WEEK):
        date = sept_14 + timedelta(days=i)
        print(f"   {i+1}. {day}: {date}")

def main():
    print("🔍 WEEK START DAY CHECKER")
    print("=" * 50)
    print(f"📅 Analysis date: {datetime.now().date()}")
    print()
    
    check_week_start()
    
    print("\n✅ WEEK START ANALYSIS COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()
