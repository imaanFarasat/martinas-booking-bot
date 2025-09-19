#!/usr/bin/env python3
"""
Initialize production database with current week data
This script will be called when the bot starts to ensure data is available
"""

import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DAYS_OF_WEEK
from database_factory import get_database_manager

def initialize_production_data():
    """Initialize the production database with current week data"""
    print("🚀 Initializing production database with current week data...")
    
    # Current week data (September 14-20, 2025) - CORRECTED VERSION
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
    
    # Get database manager (works with MySQL, PostgreSQL, or SQLite)
    db = get_database_manager()
    
    try:
        # Force delete existing data and recreate with correct data
        print(f"🗑️ Deleting any existing schedules for week: {week_start} to {week_dates['Saturday']}")
        
        # Delete existing schedules for this week
        deleted_count = 0
        for day in DAYS_OF_WEEK:
            schedule_date = week_dates[day]
            # Use the database manager's delete method
            try:
                # Get all schedules for this date and delete them
                all_schedules = db.get_all_schedules()
                for schedule in all_schedules:
                    if len(schedule) >= 3 and schedule[2]:
                        try:
                            schedule_date_str = str(schedule[2])
                            if hasattr(schedule[2], 'date'):
                                schedule_date_obj = schedule[2].date()
                            else:
                                schedule_date_obj = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
                            
                            if schedule_date_obj == schedule_date:
                                # Delete this schedule
                                db.delete_schedule(schedule[1], schedule[0])  # staff_id, day_of_week
                                deleted_count += 1
                        except:
                            continue
            except:
                continue
        
        print(f"   ✅ Deleted {deleted_count} existing schedules")
        
        print(f"📅 Initializing data for week: {week_start} to {week_dates['Saturday']}")
        
        # Add staff members and schedules
        for staff_name, schedule in current_week_data.items():
            # Add staff member if not exists
            all_staff = db.get_all_staff()
            staff_id = None
            
            for sid, sname in all_staff:
                if sname == staff_name:
                    staff_id = sid
                    break
            
            if staff_id:
                print(f"   ℹ️ Staff {staff_name} already exists (ID: {staff_id})")
            else:
                # Add new staff member
                db.add_staff(staff_name)
                # Get the new staff ID
                all_staff = db.get_all_staff()
                for sid, sname in all_staff:
                    if sname == staff_name:
                        staff_id = sid
                        break
                print(f"   ✅ Added staff {staff_name} (ID: {staff_id})")
            
            # Add schedules for this staff member
            for day, time_slot in schedule.items():
                schedule_date = week_dates[day]
                
                if time_slot == 'Off':
                    is_working = False
                    start_time = ''
                    end_time = ''
                else:
                    is_working = True
                    start_time, end_time = time_slot.split('-')
                
                # Add the schedule using the database manager
                try:
                    db.save_schedule(staff_id, day, is_working, start_time, end_time, schedule_date)
                except Exception as e:
                    print(f"   ⚠️ Could not add schedule for {staff_name} on {day}: {e}")
        
        print(f"✅ Successfully initialized production database!")
        
        # Verify the data
        all_schedules = db.get_all_schedules()
        count = 0
        for schedule in all_schedules:
            if len(schedule) >= 3 and schedule[2]:
                try:
                    schedule_date_str = str(schedule[2])
                    if hasattr(schedule[2], 'date'):
                        schedule_date_obj = schedule[2].date()
                    else:
                        schedule_date_obj = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
                    
                    if week_start <= schedule_date_obj <= week_dates['Saturday']:
                        count += 1
                except:
                    continue
        
        print(f"📊 Total schedules added: {count}")
        
    except Exception as e:
        print(f"❌ Error initializing data: {e}")
        raise

if __name__ == "__main__":
    initialize_production_data()
