#!/usr/bin/env python3
"""
Debug why current week export shows "No schedules found" but export all shows wrong data
"""

import sys
import os
from datetime import datetime, timedelta
import sqlite3
import pytz

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_PATH, DAYS_OF_WEEK

def debug_export_issue():
    """Debug the export issue"""
    print("🔍 DEBUGGING EXPORT ISSUE")
    print("=" * 60)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all schedules
    cursor.execute("""
        SELECT s.name, sch.day_of_week, sch.schedule_date, sch.is_working, sch.start_time, sch.end_time
        FROM staff s
        JOIN schedules sch ON s.id = sch.staff_id
        ORDER BY sch.schedule_date, s.name
    """)
    
    all_schedules = cursor.fetchall()
    print(f"📊 Total schedules in database: {len(all_schedules)}")
    
    # Show all unique dates
    cursor.execute("SELECT DISTINCT schedule_date FROM schedules ORDER BY schedule_date")
    all_dates = cursor.fetchall()
    print(f"\n📅 All dates in database:")
    for date_tuple in all_dates:
        print(f"   {date_tuple[0]}")
    
    # Calculate what the bot thinks is the current week
    toronto_tz = pytz.timezone('America/Toronto')
    today = datetime.now(toronto_tz).date()
    
    days_since_sunday = (today.weekday() + 1) % 7
    current_week_start = today - timedelta(days=days_since_sunday)
    if today.weekday() == 6:  # Sunday
        current_week_start = today
    
    current_week_end = current_week_start + timedelta(days=6)
    
    print(f"\n📅 Bot's current week calculation:")
    print(f"   Week starts: {current_week_start}")
    print(f"   Week ends: {current_week_end}")
    
    # Check what schedules exist for the current week
    cursor.execute("""
        SELECT s.name, sch.day_of_week, sch.schedule_date, sch.is_working, sch.start_time, sch.end_time
        FROM staff s
        JOIN schedules sch ON s.id = sch.staff_id
        WHERE sch.schedule_date BETWEEN ? AND ?
        ORDER BY s.name, sch.day_of_week
    """, (current_week_start.strftime('%Y-%m-%d'), current_week_end.strftime('%Y-%m-%d')))
    
    current_week_schedules = cursor.fetchall()
    print(f"\n📊 Schedules for current week ({current_week_start} to {current_week_end}): {len(current_week_schedules)}")
    
    if current_week_schedules:
        print(f"✅ Current week schedules found:")
        for staff_name, day, date, working, start, end in current_week_schedules[:5]:
            time_display = f"{start}-{end}" if working and start and end else "Off"
            print(f"   {staff_name} - {day} {date}: {time_display}")
    else:
        print(f"❌ No current week schedules found!")
    
    # Check what schedules exist for other weeks
    cursor.execute("""
        SELECT DISTINCT schedule_date, COUNT(*) as count
        FROM schedules 
        GROUP BY schedule_date
        ORDER BY schedule_date
    """)
    
    schedules_by_date = cursor.fetchall()
    print(f"\n📊 Schedules by date:")
    for date, count in schedules_by_date:
        if current_week_start <= datetime.strptime(date, '%Y-%m-%d').date() <= current_week_end:
            print(f"   {date}: {count} schedules ← CURRENT WEEK")
        else:
            print(f"   {date}: {count} schedules")
    
    # Simulate the export_pdf_for_week filtering logic
    print(f"\n🔍 SIMULATING EXPORT_PDF_FOR_WEEK LOGIC:")
    print(f"   Looking for schedules between: {current_week_start} and {current_week_end}")
    
    week_schedules = []
    for schedule in all_schedules:
        if len(schedule) >= 3 and schedule[2]:  # schedule_date exists
            try:
                schedule_date_str = str(schedule[2])
                schedule_date = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
                
                if current_week_start <= schedule_date <= current_week_end:
                    week_schedules.append(schedule)
                    print(f"   ✅ Added: {schedule[0]} on {schedule[1]} ({schedule_date})")
            except (ValueError, TypeError) as e:
                print(f"   ❌ Error parsing date '{schedule[2]}': {e}")
                continue
    
    print(f"\n📊 Filtered schedules for current week: {len(week_schedules)}")
    
    if len(week_schedules) == 0:
        print(f"❌ This explains why 'No schedules found for current week'")
    else:
        print(f"✅ This should work for current week export")
    
    # Check what export_all_schedules would show
    print(f"\n🔍 EXPORT_ALL_SCHEDULES would show:")
    print(f"   Total schedules: {len(all_schedules)}")
    
    # Show sample of what export_all would show
    if all_schedules:
        print(f"   Sample schedules:")
        for schedule in all_schedules[:5]:
            staff_name, day, date, working, start, end = schedule
            time_display = f"{start}-{end}" if working and start and end else "Off"
            print(f"     {staff_name} - {day} {date}: {time_display}")
    
    conn.close()
    
    print(f"\n💡 DIAGNOSIS:")
    if len(current_week_schedules) == 0:
        print(f"   ❌ The issue is that there are NO schedules for the current week")
        print(f"   📅 Bot is looking for: {current_week_start} to {current_week_end}")
        print(f"   📊 But schedules exist for other dates")
        print(f"   🔧 Solution: The database needs schedules for the current week dates")
    else:
        print(f"   ✅ Current week schedules exist")
        print(f"   🔧 The issue might be in the filtering logic or date format")

if __name__ == "__main__":
    debug_export_issue()
