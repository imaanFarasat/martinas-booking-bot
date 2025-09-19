#!/usr/bin/env python3
"""
Simple data fix - directly update the database with correct data
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_PATH, DAYS_OF_WEEK

def simple_data_fix():
    """Simple fix to update the database with correct data"""
    print("🔧 SIMPLE DATA FIX")
    print("=" * 50)
    
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
    
    print(f"📅 Updating data for week: {week_start} to {week_dates['Saturday']}")
    
    # Use a different approach - create a new database file
    new_db_path = 'shared_scheduler_fixed.db'
    
    conn = sqlite3.connect(new_db_path)
    cursor = conn.cursor()
    
    try:
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER,
                day_of_week TEXT NOT NULL,
                schedule_date DATE,
                is_working BOOLEAN NOT NULL,
                start_time TEXT,
                end_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff (id),
                UNIQUE(staff_id, day_of_week, schedule_date)
            )
        ''')
        
        # Add staff members
        staff_ids = {}
        for staff_name in correct_data.keys():
            cursor.execute('''
                INSERT OR IGNORE INTO staff (name, created_at)
                VALUES (?, datetime('now'))
            ''', (staff_name,))
            
            cursor.execute('SELECT id FROM staff WHERE name = ?', (staff_name,))
            staff_id = cursor.fetchone()[0]
            staff_ids[staff_name] = staff_id
            print(f"   ✅ Staff {staff_name} (ID: {staff_id})")
        
        # Add schedules
        for staff_name, schedule in correct_data.items():
            staff_id = staff_ids[staff_name]
            
            for day, time_slot in schedule.items():
                schedule_date = week_dates[day]
                
                if time_slot == 'Off':
                    is_working = 0
                    start_time = ''
                    end_time = ''
                else:
                    is_working = 1
                    start_time, end_time = time_slot.split('-')
                
                cursor.execute('''
                    INSERT OR REPLACE INTO schedules 
                    (staff_id, day_of_week, schedule_date, is_working, start_time, end_time, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                ''', (staff_id, day, schedule_date.strftime('%Y-%m-%d'), is_working, start_time, end_time))
        
        conn.commit()
        print(f"✅ Successfully created fixed database: {new_db_path}")
        
        # Verify the data
        cursor.execute("""
            SELECT COUNT(*) FROM schedules 
            WHERE schedule_date BETWEEN ? AND ?
        """, (week_start.strftime('%Y-%m-%d'), week_dates['Saturday'].strftime('%Y-%m-%d')))
        
        count = cursor.fetchone()[0]
        print(f"📊 Total schedules in fixed database: {count}")
        
        # Show sample data
        cursor.execute("""
            SELECT s.name, sch.day_of_week, sch.schedule_date, sch.is_working, sch.start_time, sch.end_time
            FROM staff s
            JOIN schedules sch ON s.id = sch.staff_id
            WHERE sch.schedule_date BETWEEN ? AND ?
            ORDER BY s.name, sch.day_of_week
            LIMIT 5
        """, (week_start.strftime('%Y-%m-%d'), week_dates['Saturday'].strftime('%Y-%m-%d')))
        
        sample_schedules = cursor.fetchall()
        print(f"\n📋 Sample data:")
        for staff_name, day, date, working, start, end in sample_schedules:
            time_display = f"{start}-{end}" if working and start and end else "Off"
            print(f"   {staff_name} - {day} {date}: {time_display}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        conn.close()
    
    print(f"\n💡 SOLUTION:")
    print(f"   1. Replace the old database with the fixed one:")
    print(f"      mv {new_db_path} {DATABASE_PATH}")
    print(f"   2. Or update the config to use the fixed database")
    print(f"   3. Restart the bot")

if __name__ == "__main__":
    simple_data_fix()
