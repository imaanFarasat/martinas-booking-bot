#!/usr/bin/env python3
"""
Check what happened to the missing data for September 14-20
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
import pytz

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_PATH

def check_missing_data():
    """Check what happened to the missing data"""
    print("🔍 CHECKING MISSING DATA FOR SEPTEMBER 14-20")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check for any schedules in September 14-20
        cursor.execute("""
            SELECT s.staff_id, st.name, s.day_of_week, s.schedule_date, 
                   s.is_working, s.start_time, s.end_time, s.created_at, s.updated_at
            FROM schedules s
            JOIN staff st ON s.staff_id = st.id
            WHERE s.schedule_date >= '2025-09-14' AND s.schedule_date <= '2025-09-20'
            ORDER BY s.schedule_date, st.name
        """)
        
        current_week_schedules = cursor.fetchall()
        
        if current_week_schedules:
            print(f"✅ Found {len(current_week_schedules)} schedules for September 14-20:")
            for schedule in current_week_schedules:
                staff_name = schedule[1]
                day = schedule[2]
                schedule_date = schedule[3]
                is_working = schedule[4]
                start_time = schedule[5]
                end_time = schedule[6]
                created = schedule[7]
                updated = schedule[8]
                
                if is_working:
                    time_info = f"{start_time}-{end_time}" if start_time and end_time else "Not Set"
                else:
                    time_info = "OFF"
                
                print(f"   {staff_name} ({day} {schedule_date}): {time_info}")
                print(f"      Created: {created}, Updated: {updated}")
        else:
            print("❌ No schedules found for September 14-20")
        
        # Check for any deleted schedules in the audit log
        print(f"\n🔍 CHECKING AUDIT LOG FOR DELETIONS:")
        print("=" * 70)
        
        cursor.execute("""
            SELECT sc.staff_id, st.name, sc.action, sc.day_of_week, 
                   sc.old_data, sc.new_data, sc.changed_by, sc.changed_at
            FROM schedule_changes sc
            JOIN staff st ON sc.staff_id = st.id
            WHERE sc.changed_at >= '2025-09-14'
            ORDER BY sc.changed_at DESC
        """)
        
        recent_changes = cursor.fetchall()
        
        if recent_changes:
            print(f"📝 Recent changes since September 14:")
            for change in recent_changes:
                staff_name = change[1]
                action = change[2]
                day = change[3]
                old_data = change[4]
                new_data = change[5]
                changed_by = change[6]
                changed_at = change[7]
                
                print(f"   {staff_name} - {action} - {day}")
                print(f"   Changed by: {changed_by}, When: {changed_at}")
                if old_data:
                    print(f"   Old: {old_data}")
                if new_data:
                    print(f"   New: {new_data}")
                print()
        else:
            print("❌ No recent changes found in audit log")
        
        # Check for any schedules with NULL dates
        print(f"\n🔍 CHECKING FOR SCHEDULES WITH NULL DATES:")
        print("=" * 70)
        
        cursor.execute("""
            SELECT s.staff_id, st.name, s.day_of_week, s.schedule_date, 
                   s.is_working, s.start_time, s.end_time, s.created_at, s.updated_at
            FROM schedules s
            JOIN staff st ON s.staff_id = st.id
            WHERE s.schedule_date IS NULL
            ORDER BY s.updated_at DESC
        """)
        
        null_date_schedules = cursor.fetchall()
        
        if null_date_schedules:
            print(f"📝 Found {len(null_date_schedules)} schedules with NULL dates:")
            for schedule in null_date_schedules:
                staff_name = schedule[1]
                day = schedule[2]
                schedule_date = schedule[3]
                is_working = schedule[4]
                start_time = schedule[5]
                end_time = schedule[6]
                created = schedule[7]
                updated = schedule[8]
                
                if is_working:
                    time_info = f"{start_time}-{end_time}" if start_time and end_time else "Not Set"
                else:
                    time_info = "OFF"
                
                print(f"   {staff_name} ({day}): {time_info}")
                print(f"      Created: {created}, Updated: {updated}")
        else:
            print("❌ No schedules with NULL dates found")
        
        # Check for any database corruption or issues
        print(f"\n🔍 CHECKING DATABASE INTEGRITY:")
        print("=" * 70)
        
        cursor.execute("SELECT COUNT(*) FROM schedules")
        total_schedules = cursor.fetchone()[0]
        print(f"Total schedules in database: {total_schedules}")
        
        cursor.execute("SELECT COUNT(*) FROM schedules WHERE schedule_date IS NOT NULL")
        schedules_with_dates = cursor.fetchone()[0]
        print(f"Schedules with dates: {schedules_with_dates}")
        
        cursor.execute("SELECT COUNT(*) FROM schedules WHERE schedule_date IS NULL")
        schedules_without_dates = cursor.fetchone()[0]
        print(f"Schedules without dates: {schedules_without_dates}")
        
        # Check for any recent database operations
        print(f"\n🔍 CHECKING RECENT DATABASE OPERATIONS:")
        print("=" * 70)
        
        cursor.execute("""
            SELECT s.staff_id, st.name, s.day_of_week, s.schedule_date, 
                   s.created_at, s.updated_at
            FROM schedules s
            JOIN staff st ON s.staff_id = st.id
            WHERE s.updated_at >= '2025-09-14'
            ORDER BY s.updated_at DESC
            LIMIT 10
        """)
        
        recent_updates = cursor.fetchall()
        
        if recent_updates:
            print(f"📝 Recent schedule updates since September 14:")
            for update in recent_updates:
                staff_name = update[1]
                day = update[2]
                schedule_date = update[3]
                created = update[4]
                updated = update[5]
                
                print(f"   {staff_name} ({day} {schedule_date})")
                print(f"      Created: {created}, Updated: {updated}")
        else:
            print("❌ No recent schedule updates found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking missing data: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔍 MISSING DATA INVESTIGATION")
    print("=" * 70)
    print(f"📅 Investigation date: {datetime.now().date()}")
    print()
    
    check_missing_data()
    
    print("\n✅ MISSING DATA INVESTIGATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
