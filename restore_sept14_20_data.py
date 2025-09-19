#!/usr/bin/env python3
"""
Restore September 14-20 data from PDF to database
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
import pytz

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_factory import get_database_manager
from config import DAYS_OF_WEEK, DATABASE_PATH

def restore_sept14_20_data():
    """Restore September 14-20 data from PDF to database"""
    print("🔄 RESTORING SEPTEMBER 14-20 DATA FROM PDF")
    print("=" * 70)
    
    # Data from the PDF
    pdf_data = {
        'Asal': {
            'Sunday': '13:00-21:00',
            'Monday': '13:00-21:00', 
            'Tuesday': 'Off',
            'Wednesday': '11:00-19:00',
            'Thursday': '13:00-21:00',
            'Friday': '10:00-18:00',
            'Saturday': 'Off'
        },
        'Bea': {
            'Sunday': '09:45-18:00',
            'Monday': '09:45-18:00',
            'Tuesday': '13:00-21:00',
            'Wednesday': 'Off',
            'Thursday': 'Off',
            'Friday': '09:45-18:00',
            'Saturday': '09:45-18:00'
        },
        'Miranda': {
            'Sunday': '13:00-20:00',
            'Monday': 'Off',
            'Tuesday': 'Off',
            'Wednesday': '15:00-21:00',
            'Thursday': '15:00-21:00',
            'Friday': '15:00-21:00',
            'Saturday': '13:00-20:00'
        },
        'Mobina': {
            'Sunday': 'Off',
            'Monday': 'Off',
            'Tuesday': '15:30-21:00',
            'Wednesday': 'Off',
            'Thursday': '13:00-21:00',
            'Friday': '12:00-21:00',
            'Saturday': '13:00-21:00'
        },
        'Negar': {
            'Sunday': 'Off',
            'Monday': 'Off',
            'Tuesday': '10:00-18:00',
            'Wednesday': 'Off',
            'Thursday': '10:00-18:00',
            'Friday': 'Off',
            'Saturday': 'Off'
        },
        'Savannah': {
            'Sunday': 'Off',
            'Monday': '10:00-18:00',
            'Tuesday': '10:00-18:00',
            'Wednesday': '10:00-18:00',
            'Thursday': '10:00-18:00',
            'Friday': 'Off',
            'Saturday': 'Off'
        },
        'Trecia': {
            'Sunday': '13:00-21:00',
            'Monday': '13:00-21:00',
            'Tuesday': '13:00-21:00',
            'Wednesday': '13:00-21:00',
            'Thursday': '13:00-21:00',
            'Friday': '13:00-21:00',
            'Saturday': '13:00-21:00'
        },
        'Stacy': {
            'Sunday': '13:00-21:00',
            'Monday': '10:00-18:00',
            'Tuesday': '10:00-18:00',
            'Wednesday': '10:00-18:00',
            'Thursday': '10:00-18:00',
            'Friday': 'Off',
            'Saturday': 'Off'
        }
    }
    
    # Calculate September 14-20 dates
    toronto_tz = pytz.timezone('America/Toronto')
    sept_14 = datetime(2025, 9, 14).date()  # Sunday
    sept_20 = datetime(2025, 9, 20).date()  # Saturday
    
    print(f"📅 Restoring data for: {sept_14} to {sept_20}")
    
    # Get database manager
    db = get_database_manager()
    
    # Get staff mapping
    staff_list = db.get_all_staff()
    staff_id_map = {name: staff_id for staff_id, name in staff_list}
    
    print(f"👥 Found {len(staff_list)} staff members in database")
    
    # Use direct database connection
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    restored_count = 0
    failed_count = 0
    staff_not_found = []
    
    try:
        for staff_name, schedule in pdf_data.items():
            staff_id = staff_id_map.get(staff_name)
            
            if not staff_id:
                print(f"❌ Staff not found in database: {staff_name}")
                staff_not_found.append(staff_name)
                failed_count += 1
                continue
            
            print(f"\n👤 Restoring {staff_name} (ID: {staff_id}):")
            
            for day, time_info in schedule.items():
                # Calculate date for this day
                day_index = DAYS_OF_WEEK.index(day)
                schedule_date = sept_14 + timedelta(days=day_index)
                
                # Parse time info
                if time_info == 'Off':
                    is_working = 0
                    start_time = None
                    end_time = None
                else:
                    is_working = 1
                    if '-' in time_info:
                        start_time, end_time = time_info.split('-')
                    else:
                        start_time = time_info
                        end_time = None
                
                try:
                    # Insert schedule
                    cursor.execute('''
                        INSERT OR REPLACE INTO schedules 
                        (staff_id, day_of_week, schedule_date, is_working, start_time, end_time, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    ''', (staff_id, day, schedule_date.strftime('%Y-%m-%d'), is_working, start_time, end_time))
                    
                    restored_count += 1
                    status = time_info if time_info != 'Off' else 'OFF'
                    print(f"   ✅ {day} ({schedule_date}): {status}")
                    
                except Exception as e:
                    failed_count += 1
                    print(f"   ❌ Error restoring {day}: {e}")
        
        # Commit all changes
        conn.commit()
        print(f"\n💾 All changes committed to database")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during restore operation: {e}")
    finally:
        conn.close()
    
    # Summary
    print(f"\n📊 RESTORE SUMMARY:")
    print(f"✅ Successfully restored: {restored_count} schedules")
    print(f"❌ Failed: {failed_count}")
    print(f"👥 Staff processed: {len(pdf_data)}")
    
    if staff_not_found:
        print(f"\n❌ Staff not found in database: {', '.join(staff_not_found)}")
        print("💡 You may need to add these staff members first")
    
    if restored_count > 0:
        print(f"\n🎉 SUCCESS! September 14-20 data restored!")
        print(f"📅 Week: {sept_14} to {sept_20}")
        print(f"🔄 You can now use 'Copy from Previous Week' feature!")
    
    return {
        'restored': restored_count,
        'failed': failed_count,
        'staff_not_found': staff_not_found
    }

def main():
    print("🔄 SEPTEMBER 14-20 DATA RESTORATION")
    print("=" * 70)
    print(f"📅 Restoration date: {datetime.now().date()}")
    print()
    
    result = restore_sept14_20_data()
    
    print("\n✅ DATA RESTORATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
