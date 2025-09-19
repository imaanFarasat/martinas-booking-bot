#!/usr/bin/env python3
"""
Force update the database with the correct current week data
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_PATH, DAYS_OF_WEEK

def force_update_correct_data():
    """Force update the database with the correct current week data"""
    print("🔄 FORCE UPDATING DATABASE WITH CORRECT DATA")
    print("=" * 60)
    
    # CORRECT current week data (September 14-20, 2025)
    correct_data = {
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
    
    # Week dates (September 14-20, 2025)
    week_start = datetime(2025, 9, 14).date()  # Sunday
    week_dates = {}
    
    for i, day in enumerate(DAYS_OF_WEEK):
        week_dates[day] = week_start + timedelta(days=i)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN TRANSACTION")
        
        print(f"🗑️ Deleting all existing schedules for week: {week_start} to {week_dates['Saturday']}")
        
        # Delete all existing schedules for this week
        cursor.execute("""
            DELETE FROM schedules 
            WHERE schedule_date BETWEEN ? AND ?
        """, (week_start.strftime('%Y-%m-%d'), week_dates['Saturday'].strftime('%Y-%m-%d')))
        
        deleted_count = cursor.rowcount
        print(f"   ✅ Deleted {deleted_count} existing schedules")
        
        print(f"📝 Adding correct schedules...")
        
        # Add correct schedules for each staff member
        for staff_name, schedule in correct_data.items():
            # Get staff ID
            cursor.execute('SELECT id FROM staff WHERE name = ?', (staff_name,))
            result = cursor.fetchone()
            
            if not result:
                print(f"   ❌ Staff {staff_name} not found!")
                continue
                
            staff_id = result[0]
            print(f"   📝 Updating {staff_name} (ID: {staff_id})")
            
            # Add schedules for this staff member
            for day, time_slot in schedule.items():
                schedule_date = week_dates[day]
                
                if time_slot == 'Off':
                    is_working = 0
                    start_time = ''
                    end_time = ''
                else:
                    is_working = 1
                    start_time, end_time = time_slot.split('-')
                
                # Insert the correct schedule
                cursor.execute('''
                    INSERT INTO schedules (staff_id, day_of_week, is_working, start_time, end_time, schedule_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                ''', (staff_id, day, is_working, start_time, end_time, schedule_date.strftime('%Y-%m-%d')))
        
        cursor.execute("COMMIT")
        print(f"✅ Successfully updated database with correct data!")
        
        # Verify the data
        cursor.execute("""
            SELECT COUNT(*) FROM schedules 
            WHERE schedule_date BETWEEN ? AND ?
        """, (week_start.strftime('%Y-%m-%d'), week_dates['Saturday'].strftime('%Y-%m-%d')))
        
        count = cursor.fetchone()[0]
        print(f"📊 Total schedules now in database: {count}")
        
        # Show sample of updated data
        cursor.execute("""
            SELECT s.name, sch.day_of_week, sch.schedule_date, sch.is_working, sch.start_time, sch.end_time
            FROM staff s
            JOIN schedules sch ON s.id = sch.staff_id
            WHERE sch.schedule_date BETWEEN ? AND ?
            ORDER BY s.name, sch.day_of_week
            LIMIT 10
        """, (week_start.strftime('%Y-%m-%d'), week_dates['Saturday'].strftime('%Y-%m-%d')))
        
        sample_schedules = cursor.fetchall()
        print(f"\n📋 Sample of updated schedules:")
        for staff_name, day, date, working, start, end in sample_schedules:
            time_display = f"{start}-{end}" if working and start and end else "Off"
            print(f"   {staff_name} - {day} {date}: {time_display}")
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"❌ Error updating data: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    force_update_correct_data()
