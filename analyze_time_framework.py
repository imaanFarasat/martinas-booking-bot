#!/usr/bin/env python3
"""
Analyze the time framework issue - why the system doesn't understand the time context
"""

import sys
import os
from datetime import datetime, timedelta
import pytz

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_time_framework():
    """Analyze the time framework and week calculation logic"""
    print("🔍 ANALYZING TIME FRAMEWORK ISSUE")
    print("=" * 70)
    
    # Current date
    toronto_tz = pytz.timezone('America/Toronto')
    today = datetime.now(toronto_tz).date()
    print(f"📅 Today: {today} ({today.strftime('%A')})")
    
    # Calculate current week using the system's logic
    days_since_sunday = (today.weekday() + 1) % 7
    current_week_start = today - timedelta(days=days_since_sunday)
    if today.weekday() == 6:  # Sunday
        current_week_start = today
    
    current_week_end = current_week_start + timedelta(days=6)
    
    print(f"📅 Current week (system calculation): {current_week_start} to {current_week_end}")
    
    # Calculate previous week
    previous_week_start = current_week_start - timedelta(days=7)
    previous_week_end = previous_week_start + timedelta(days=6)
    
    print(f"📅 Previous week (system calculation): {previous_week_start} to {previous_week_end}")
    
    # Show the actual data dates
    print(f"\n📊 ACTUAL DATA SITUATION:")
    print("=" * 70)
    print(f"📅 Your client's data: September 7-13, 2025")
    print(f"📅 Today: September 19, 2025")
    print(f"📅 System thinks current week: September 14-20, 2025")
    print(f"📅 System thinks previous week: September 7-13, 2025")
    
    # Calculate the gap
    data_week_end = datetime(2025, 9, 13).date()
    today_date = datetime(2025, 9, 19).date()
    gap_days = (today_date - data_week_end).days
    
    print(f"\n⏰ TIME GAP ANALYSIS:")
    print("=" * 70)
    print(f"📅 Data ends: {data_week_end}")
    print(f"📅 Today: {today_date}")
    print(f"📅 Gap: {gap_days} days")
    print(f"📅 Gap in weeks: {gap_days / 7:.1f} weeks")
    
    # Show what the system is looking for vs what exists
    print(f"\n🔍 SYSTEM LOGIC PROBLEM:")
    print("=" * 70)
    print(f"❌ System looks for: Current week (Sept 14-20)")
    print(f"❌ System finds: Nothing (0 schedules)")
    print(f"✅ Data exists in: Previous week (Sept 7-13)")
    print(f"✅ Data amount: 63 schedules")
    
    # Show the week calculation breakdown
    print(f"\n📊 WEEK CALCULATION BREAKDOWN:")
    print("=" * 70)
    print(f"Today: {today} (day {today.weekday()})")
    print(f"Days since Sunday: {days_since_sunday}")
    print(f"Week start calculation: {today} - {days_since_sunday} days = {current_week_start}")
    
    # Show what should happen
    print(f"\n💡 WHAT SHOULD HAPPEN:")
    print("=" * 70)
    print(f"Option 1: Copy Sept 7-13 data to Sept 14-20 (current week)")
    print(f"Option 2: Modify PDF to show Sept 7-13 data (where data exists)")
    print(f"Option 3: Fix the week calculation logic")
    
    # Show the actual week boundaries
    print(f"\n📅 ACTUAL WEEK BOUNDARIES:")
    print("=" * 70)
    weeks = []
    for i in range(-2, 3):  # 2 weeks before, current, 2 weeks after
        week_start = current_week_start + timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        weeks.append((week_start, week_end, f"Week {i+3}"))
    
    for week_start, week_end, week_name in weeks:
        if week_start <= datetime(2025, 9, 13).date() <= week_end:
            print(f"📅 {week_name}: {week_start} to {week_end} ← YOUR DATA IS HERE")
        elif week_start <= today <= week_end:
            print(f"📅 {week_name}: {week_start} to {week_end} ← TODAY IS HERE")
        else:
            print(f"📅 {week_name}: {week_start} to {week_end}")

def analyze_week_calculation_logic():
    """Analyze the week calculation logic in detail"""
    print(f"\n🔍 WEEK CALCULATION LOGIC ANALYSIS:")
    print("=" * 70)
    
    toronto_tz = pytz.timezone('America/Toronto')
    today = datetime.now(toronto_tz).date()
    
    print(f"Today: {today} ({today.strftime('%A')})")
    print(f"Today.weekday(): {today.weekday()} (0=Monday, 6=Sunday)")
    
    # Show the calculation step by step
    print(f"\nStep-by-step calculation:")
    print(f"1. today.weekday() = {today.weekday()}")
    print(f"2. days_since_sunday = (today.weekday() + 1) % 7")
    print(f"3. days_since_sunday = ({today.weekday()} + 1) % 7 = {(today.weekday() + 1) % 7}")
    print(f"4. week_start = today - {days_since_sunday} days")
    
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    
    print(f"5. week_start = {today} - {days_since_sunday} days = {week_start}")
    
    # Check if this is correct
    print(f"\nVerification:")
    print(f"Week start: {week_start} ({week_start.strftime('%A')})")
    print(f"Week end: {week_start + timedelta(days=6)} ({(week_start + timedelta(days=6)).strftime('%A')})")
    
    # Show what the data week should be
    data_week_start = datetime(2025, 9, 7).date()  # Sunday
    data_week_end = datetime(2025, 9, 13).date()   # Saturday
    
    print(f"\nData week:")
    print(f"Data week start: {data_week_start} ({data_week_start.strftime('%A')})")
    print(f"Data week end: {data_week_end} ({data_week_end.strftime('%A')})")
    
    # Calculate how many weeks apart
    weeks_apart = (week_start - data_week_start).days / 7
    print(f"\nWeeks apart: {weeks_apart} weeks")
    
    if weeks_apart == 1:
        print("✅ Data is exactly 1 week before current week")
    elif weeks_apart > 1:
        print(f"❌ Data is {weeks_apart} weeks before current week")
    else:
        print(f"❌ Data is {weeks_apart} weeks after current week")

def main():
    print("🔍 TIME FRAMEWORK ANALYSIS")
    print("=" * 70)
    print(f"📅 Analysis date: {datetime.now().date()}")
    print()
    
    analyze_time_framework()
    analyze_week_calculation_logic()
    
    print("\n✅ TIME FRAMEWORK ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
