#!/usr/bin/env python3
"""
Find Lost Data - Check database for any traces of September 14-20 data
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
import pytz

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_PATH

def find_lost_data():
    """Search for any traces of September 14-20 data"""
    print("🔍 SEARCHING FOR LOST SEPTEMBER 14-20 DATA")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check for any schedules in September 14-20
        print("🔍 Checking for September 14-20 schedules...")
        cursor.execute("""
            SELECT s.staff_id, st.name, s.day_of_week, s.schedule_date, 
                   s.is_working, s.start_time, s.end_time, s.created_at, s.updated_at
            FROM schedules s
            JOIN staff st ON s.staff_id = st.id
            WHERE s.schedule_date >= '2025-09-14' AND s.schedule_date <= '2025-09-20'
            ORDER BY s.schedule_date, st.name
        """)
        
        sept_14_20_schedules = cursor.fetchall()
        
        if sept_14_20_schedules:
            print(f"✅ Found {len(sept_14_20_schedules)} schedules for September 14-20!")
            for schedule in sept_14_20_schedules:
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
        
        # Check for any schedules with NULL dates that might be from that week
        print(f"\n🔍 Checking for schedules with NULL dates...")
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
        
        # Check for any recent changes in the audit log
        print(f"\n🔍 Checking audit log for recent changes...")
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
            print(f"📝 Found {len(recent_changes)} recent changes since September 14:")
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
        
        # Check for any schedules created or updated in September 14-20 timeframe
        print(f"\n🔍 Checking for schedules created/updated in September 14-20 timeframe...")
        cursor.execute("""
            SELECT s.staff_id, st.name, s.day_of_week, s.schedule_date, 
                   s.is_working, s.start_time, s.end_time, s.created_at, s.updated_at
            FROM schedules s
            JOIN staff st ON s.staff_id = st.id
            WHERE (s.created_at >= '2025-09-14' AND s.created_at <= '2025-09-20 23:59:59')
               OR (s.updated_at >= '2025-09-14' AND s.updated_at <= '2025-09-20 23:59:59')
            ORDER BY s.updated_at DESC
        """)
        
        timeframe_schedules = cursor.fetchall()
        
        if timeframe_schedules:
            print(f"📝 Found {len(timeframe_schedules)} schedules created/updated in September 14-20 timeframe:")
            for schedule in timeframe_schedules:
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
            print("❌ No schedules found in September 14-20 timeframe")
        
        # Check for any deleted schedules in the audit log
        print(f"\n🔍 Checking for deleted schedules...")
        cursor.execute("""
            SELECT sc.staff_id, st.name, sc.action, sc.day_of_week, 
                   sc.old_data, sc.new_data, sc.changed_by, sc.changed_at
            FROM schedule_changes sc
            JOIN staff st ON sc.staff_id = st.id
            WHERE sc.action LIKE '%DELETE%' OR sc.action LIKE '%REMOVE%'
            ORDER BY sc.changed_at DESC
        """)
        
        deleted_schedules = cursor.fetchall()
        
        if deleted_schedules:
            print(f"📝 Found {len(deleted_schedules)} deleted schedules:")
            for change in deleted_schedules:
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
            print("❌ No deleted schedules found in audit log")
        
        # Check database file modification time
        print(f"\n🔍 Checking database file info...")
        if os.path.exists(DATABASE_PATH):
            stat = os.stat(DATABASE_PATH)
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            created_time = datetime.fromtimestamp(stat.st_ctime)
            file_size = stat.st_size
            
            print(f"📄 Database file: {DATABASE_PATH}")
            print(f"📏 File size: {file_size} bytes")
            print(f"📅 Created: {created_time}")
            print(f"📅 Last modified: {modified_time}")
            
            # Check if file was modified around September 14-20
            sept_14 = datetime(2025, 9, 14)
            sept_20 = datetime(2025, 9, 20, 23, 59, 59)
            
            if sept_14 <= modified_time <= sept_20:
                print(f"✅ Database was modified during September 14-20 timeframe!")
            else:
                print(f"❌ Database was not modified during September 14-20 timeframe")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error searching for lost data: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔍 LOST DATA RECOVERY TOOL")
    print("=" * 70)
    print(f"📅 Search date: {datetime.now().date()}")
    print()
    
    find_lost_data()
    
    print("\n✅ LOST DATA SEARCH COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
