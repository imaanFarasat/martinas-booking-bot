#!/usr/bin/env python3
"""
Check what data is actually in the production database
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_PATH, DAYS_OF_WEEK

def check_production_data():
    """Check what data is actually in the database"""
    print("🔍 CHECKING PRODUCTION DATABASE DATA")
    print("=" * 60)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check total staff count
    cursor.execute("SELECT COUNT(*) FROM staff")
    total_staff = cursor.fetchone()[0]
    print(f"👥 Total staff in database: {total_staff}")
    
    # List all staff
    cursor.execute("SELECT id, name FROM staff ORDER BY name")
    all_staff = cursor.fetchall()
    print(f"\n📋 All staff members:")
    for staff_id, staff_name in all_staff:
        print(f"   {staff_id}: {staff_name}")
    
    # Check total schedules
    cursor.execute("SELECT COUNT(*) FROM schedules")
    total_schedules = cursor.fetchone()[0]
    print(f"\n📅 Total schedules in database: {total_schedules}")
    
    # Check schedules by date range
    cursor.execute("""
        SELECT schedule_date, COUNT(*) as count
        FROM schedules 
        GROUP BY schedule_date
        ORDER BY schedule_date
    """)
    
    schedules_by_date = cursor.fetchall()
    print(f"\n📊 Schedules by date:")
    for date, count in schedules_by_date:
        print(f"   {date}: {count} schedules")
    
    # Check current week specifically (Sept 14-20, 2025)
    current_week_start = '2025-09-14'
    current_week_end = '2025-09-20'
    
    cursor.execute("""
        SELECT COUNT(*) FROM schedules 
        WHERE schedule_date BETWEEN ? AND ?
    """, (current_week_start, current_week_end))
    
    current_week_count = cursor.fetchone()[0]
    print(f"\n📅 Current week schedules (Sept 14-20): {current_week_count}")
    
    if current_week_count > 0:
        # Show which staff have current week schedules
        cursor.execute("""
            SELECT DISTINCT s.name, COUNT(sch.id) as schedule_count
            FROM staff s
            JOIN schedules sch ON s.id = sch.staff_id
            WHERE sch.schedule_date BETWEEN ? AND ?
            GROUP BY s.id, s.name
            ORDER BY s.name
        """, (current_week_start, current_week_end))
        
        staff_with_schedules = cursor.fetchall()
        print(f"👥 Staff with current week schedules:")
        for staff_name, schedule_count in staff_with_schedules:
            print(f"   {staff_name}: {schedule_count} schedules")
        
        # Show sample schedules
        cursor.execute("""
            SELECT s.name, sch.day_of_week, sch.schedule_date, sch.is_working, sch.start_time, sch.end_time
            FROM staff s
            JOIN schedules sch ON s.id = sch.staff_id
            WHERE sch.schedule_date BETWEEN ? AND ?
            ORDER BY s.name, sch.day_of_week
            LIMIT 10
        """, (current_week_start, current_week_end))
        
        sample_schedules = cursor.fetchall()
        print(f"\n📋 Sample current week schedules:")
        for staff_name, day, date, working, start, end in sample_schedules:
            time_display = f"{start}-{end}" if working and start and end else "Off"
            print(f"   {staff_name} - {day} {date}: {time_display}")
    
    # Check if there are any schedules at all
    if total_schedules == 0:
        print(f"\n❌ NO SCHEDULES FOUND IN DATABASE!")
        print(f"   This explains why the bot shows 'No Current Week Found'")
    elif current_week_count == 0:
        print(f"\n❌ NO CURRENT WEEK SCHEDULES FOUND!")
        print(f"   The database has {total_schedules} schedules, but none for current week")
        print(f"   This explains why the bot shows 'No Current Week Found'")
    else:
        print(f"\n✅ CURRENT WEEK DATA FOUND!")
        print(f"   The bot should be able to find and export this data")
    
    conn.close()

if __name__ == "__main__":
    check_production_data()
