#!/usr/bin/env python3
"""
Initialize production database with current week data
This script will be called when the bot starts to ensure data is available
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_PATH, DAYS_OF_WEEK

def initialize_production_data():
    """Initialize the production database with current week data"""
    print("🚀 Initializing production database with current week data...")
    
    # Current week data (September 14-20, 2025)
    current_week_data = {
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
        
        # Check if data already exists
        cursor.execute("""
            SELECT COUNT(*) FROM schedules 
            WHERE schedule_date BETWEEN ? AND ?
        """, (week_start.strftime('%Y-%m-%d'), week_dates['Saturday'].strftime('%Y-%m-%d')))
        
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"✅ Data already exists ({existing_count} schedules). Skipping initialization.")
            cursor.execute("COMMIT")
            conn.close()
            return
        
        print(f"📅 Initializing data for week: {week_start} to {week_dates['Saturday']}")
        
        # Add staff members and schedules
        for staff_name, schedule in current_week_data.items():
            # Add staff member if not exists
            cursor.execute('SELECT id FROM staff WHERE name = ?', (staff_name,))
            result = cursor.fetchone()
            
            if result:
                staff_id = result[0]
                print(f"   ℹ️ Staff {staff_name} already exists (ID: {staff_id})")
            else:
                cursor.execute('''
                    INSERT INTO staff (name, created_at)
                    VALUES (?, datetime('now'))
                ''', (staff_name,))
                staff_id = cursor.lastrowid
                print(f"   ✅ Added staff {staff_name} (ID: {staff_id})")
            
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
                
                # Delete any existing schedule for this staff and day
                cursor.execute('''
                    DELETE FROM schedules 
                    WHERE staff_id = ? AND day_of_week = ?
                ''', (staff_id, day))
                
                # Insert the new schedule
                cursor.execute('''
                    INSERT INTO schedules (staff_id, day_of_week, is_working, start_time, end_time, schedule_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                ''', (staff_id, day, is_working, start_time, end_time, schedule_date.strftime('%Y-%m-%d')))
        
        cursor.execute("COMMIT")
        print(f"✅ Successfully initialized production database!")
        
        # Verify the data
        cursor.execute("""
            SELECT COUNT(*) FROM schedules 
            WHERE schedule_date BETWEEN ? AND ?
        """, (week_start.strftime('%Y-%m-%d'), week_dates['Saturday'].strftime('%Y-%m-%d')))
        
        count = cursor.fetchone()[0]
        print(f"📊 Total schedules added: {count}")
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"❌ Error initializing data: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_production_data()
