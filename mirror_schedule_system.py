#!/usr/bin/env python3
"""
Mirror Schedule System - Copy previous/current week to next week with editing capabilities
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

class ScheduleMirror:
    def __init__(self):
        self.db = get_database_manager()
        self.toronto_tz = pytz.timezone('America/Toronto')
    
    def get_week_dates(self, week_start):
        """Get all dates for a week starting from week_start"""
        week_dates = {}
        for i, day in enumerate(DAYS_OF_WEEK):
            week_dates[day] = week_start + timedelta(days=i)
        return week_dates
    
    def get_current_week_start(self):
        """Get current week start (Sunday)"""
        today = datetime.now(self.toronto_tz).date()
        days_since_sunday = (today.weekday() + 1) % 7
        week_start = today - timedelta(days=days_since_sunday)
        if today.weekday() == 6:  # Sunday
            week_start = today
        return week_start
    
    def get_previous_week_start(self):
        """Get previous week start (Sunday)"""
        current_week_start = self.get_current_week_start()
        return current_week_start - timedelta(days=7)
    
    def get_next_week_start(self):
        """Get next week start (Sunday)"""
        current_week_start = self.get_current_week_start()
        return current_week_start + timedelta(days=7)
    
    def get_week_schedules(self, week_start):
        """Get all schedules for a specific week"""
        week_dates = self.get_week_dates(week_start)
        week_end = week_start + timedelta(days=6)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.staff_id, st.name, s.day_of_week, s.schedule_date, 
                   s.is_working, s.start_time, s.end_time
            FROM schedules s
            JOIN staff st ON s.staff_id = st.id
            WHERE s.schedule_date >= ? AND s.schedule_date <= ?
            ORDER BY s.schedule_date, st.name
        """, (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
        
        schedules = cursor.fetchall()
        conn.close()
        
        return schedules
    
    def display_week_schedules(self, week_start, week_name):
        """Display schedules for a week"""
        schedules = self.get_week_schedules(week_start)
        week_dates = self.get_week_dates(week_start)
        
        print(f"\n📅 {week_name} ({week_start} to {week_start + timedelta(days=6)})")
        print("=" * 60)
        
        if not schedules:
            print("❌ No schedules found for this week")
            return
        
        # Group schedules by day
        day_schedules = {}
        for schedule in schedules:
            day = schedule[2]  # day_of_week
            if day not in day_schedules:
                day_schedules[day] = []
            day_schedules[day].append(schedule)
        
        # Display by day
        for day in DAYS_OF_WEEK:
            date = week_dates[day]
            print(f"\n📅 {day} ({date}):")
            
            if day in day_schedules:
                for schedule in day_schedules[day]:
                    staff_name = schedule[1]
                    is_working = schedule[4]
                    start_time = schedule[5]
                    end_time = schedule[6]
                    
                    if is_working:
                        time_info = f"{start_time}-{end_time}" if start_time and end_time else "Not Set"
                    else:
                        time_info = "OFF"
                    
                    print(f"   👤 {staff_name}: {time_info}")
            else:
                print("   ❌ No schedules for this day")
    
    def mirror_week_schedules(self, source_week_start, target_week_start, week_name):
        """Mirror schedules from source week to target week"""
        source_schedules = self.get_week_schedules(source_week_start)
        target_week_dates = self.get_week_dates(target_week_start)
        
        print(f"\n🔄 MIRRORING {week_name}")
        print("=" * 60)
        print(f"📅 From: {source_week_start} to {source_week_start + timedelta(days=6)}")
        print(f"📅 To: {target_week_start} to {target_week_start + timedelta(days=6)}")
        
        if not source_schedules:
            print("❌ No source schedules found to mirror")
            return
        
        # Get staff mapping
        staff_list = self.db.get_all_staff()
        staff_id_map = {name: staff_id for staff_id, name in staff_list}
        
        # Use direct database connection
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        copied_count = 0
        failed_count = 0
        
        try:
            for schedule in source_schedules:
                staff_name = schedule[1]
                day = schedule[2]
                is_working = schedule[4]
                start_time = schedule[5]
                end_time = schedule[6]
                
                staff_id = staff_id_map.get(staff_name)
                if not staff_id:
                    print(f"❌ Staff ID not found for {staff_name}")
                    failed_count += 1
                    continue
                
                # Calculate new date for target week
                day_index = DAYS_OF_WEEK.index(day)
                new_date = target_week_start + timedelta(days=day_index)
                
                try:
                    # Insert schedule
                    cursor.execute('''
                        INSERT OR REPLACE INTO schedules 
                        (staff_id, day_of_week, schedule_date, is_working, start_time, end_time, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    ''', (staff_id, day, new_date.strftime('%Y-%m-%d'), is_working, start_time, end_time))
                    
                    copied_count += 1
                    status = f"{start_time}-{end_time}" if is_working else "OFF"
                    print(f"✅ {staff_name} - {day} ({new_date}): {status}")
                    
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error copying {staff_name} - {day}: {e}")
            
            # Commit all changes
            conn.commit()
            print(f"\n💾 All changes committed to database")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error during mirror operation: {e}")
        finally:
            conn.close()
        
        print(f"\n📊 MIRROR SUMMARY:")
        print(f"✅ Successfully copied: {copied_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📅 Total: {len(source_schedules)}")
        
        if copied_count > 0:
            print(f"\n🎉 SUCCESS! {week_name} mirrored to next week!")
            print(f"📅 Next week: {target_week_start} to {target_week_start + timedelta(days=6)}")
    
    def edit_day_schedule(self, target_week_start, day):
        """Edit schedules for a specific day in the target week"""
        target_week_dates = self.get_week_dates(target_week_start)
        target_date = target_week_dates[day]
        
        print(f"\n✏️ EDITING {day} ({target_date})")
        print("=" * 50)
        
        # Get current schedules for this day
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.staff_id, st.name, s.is_working, s.start_time, s.end_time
            FROM schedules s
            JOIN staff st ON s.staff_id = st.id
            WHERE s.schedule_date = ?
            ORDER BY st.name
        """, (target_date.strftime('%Y-%m-%d'),))
        
        day_schedules = cursor.fetchall()
        
        if not day_schedules:
            print("❌ No schedules found for this day")
            conn.close()
            return
        
        print(f"👥 Staff scheduled for {day} ({target_date}):")
        for i, schedule in enumerate(day_schedules):
            staff_id, staff_name, is_working, start_time, end_time = schedule
            if is_working:
                time_info = f"{start_time}-{end_time}" if start_time and end_time else "Not Set"
            else:
                time_info = "OFF"
            print(f"   {i+1}. {staff_name}: {time_info}")
        
        print(f"\nOptions:")
        print(f"1. Turn all OFF")
        print(f"2. Edit individual staff")
        print(f"3. Keep as is")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            # Turn all OFF
            for schedule in day_schedules:
                staff_id = schedule[0]
                cursor.execute('''
                    UPDATE schedules 
                    SET is_working = 0, start_time = NULL, end_time = NULL, updated_at = datetime('now')
                    WHERE staff_id = ? AND schedule_date = ?
                ''', (staff_id, target_date.strftime('%Y-%m-%d')))
            
            conn.commit()
            print("✅ All staff turned OFF for this day")
            
        elif choice == "2":
            # Edit individual staff
            for schedule in day_schedules:
                staff_id, staff_name, is_working, start_time, end_time = schedule
                
                print(f"\n👤 Editing {staff_name}:")
                print(f"   Current: {'OFF' if not is_working else f'{start_time}-{end_time}'}")
                print(f"   Options:")
                print(f"   1. Keep as is")
                print(f"   2. Turn OFF")
                print(f"   3. Change time")
                
                edit_choice = input(f"   Enter choice for {staff_name} (1-3): ").strip()
                
                if edit_choice == "2":
                    # Turn OFF
                    cursor.execute('''
                        UPDATE schedules 
                        SET is_working = 0, start_time = NULL, end_time = NULL, updated_at = datetime('now')
                        WHERE staff_id = ? AND schedule_date = ?
                    ''', (staff_id, target_date.strftime('%Y-%m-%d')))
                    print(f"   ✅ {staff_name} turned OFF")
                    
                elif edit_choice == "3":
                    # Change time
                    new_start = input(f"   Enter start time for {staff_name} (HH:MM): ").strip()
                    new_end = input(f"   Enter end time for {staff_name} (HH:MM): ").strip()
                    
                    if new_start and new_end:
                        cursor.execute('''
                            UPDATE schedules 
                            SET is_working = 1, start_time = ?, end_time = ?, updated_at = datetime('now')
                            WHERE staff_id = ? AND schedule_date = ?
                        ''', (new_start, new_end, staff_id, target_date.strftime('%Y-%m-%d')))
                        print(f"   ✅ {staff_name} updated to {new_start}-{new_end}")
                    else:
                        print(f"   ❌ Invalid time format for {staff_name}")
                
                elif edit_choice == "1":
                    print(f"   ✅ {staff_name} kept as is")
        
        elif choice == "3":
            print("✅ No changes made")
        
        conn.commit()
        conn.close()
    
    def run_mirror_system(self):
        """Main mirror system interface"""
        print("🔄 SCHEDULE MIRROR SYSTEM")
        print("=" * 60)
        
        current_week_start = self.get_current_week_start()
        previous_week_start = self.get_previous_week_start()
        next_week_start = self.get_next_week_start()
        
        print(f"📅 Current week: {current_week_start} to {current_week_start + timedelta(days=6)}")
        print(f"📅 Previous week: {previous_week_start} to {previous_week_start + timedelta(days=6)}")
        print(f"📅 Next week: {next_week_start} to {next_week_start + timedelta(days=6)}")
        
        while True:
            print(f"\n🔄 MIRROR OPTIONS:")
            print("1. View Previous Week Schedules")
            print("2. View Current Week Schedules")
            print("3. Mirror Previous Week → Next Week")
            print("4. Mirror Current Week → Next Week")
            print("5. Edit Next Week Day")
            print("6. View Next Week Schedules")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == "1":
                self.display_week_schedules(previous_week_start, "PREVIOUS WEEK")
                
            elif choice == "2":
                self.display_week_schedules(current_week_start, "CURRENT WEEK")
                
            elif choice == "3":
                self.mirror_week_schedules(previous_week_start, next_week_start, "PREVIOUS WEEK")
                
            elif choice == "4":
                self.mirror_week_schedules(current_week_start, next_week_start, "CURRENT WEEK")
                
            elif choice == "5":
                print(f"\n📅 Choose day to edit in next week:")
                for i, day in enumerate(DAYS_OF_WEEK):
                    print(f"   {i+1}. {day}")
                
                day_choice = input("Enter day number (1-7): ").strip()
                try:
                    day_index = int(day_choice) - 1
                    if 0 <= day_index < 7:
                        day = DAYS_OF_WEEK[day_index]
                        self.edit_day_schedule(next_week_start, day)
                    else:
                        print("❌ Invalid day number")
                except ValueError:
                    print("❌ Invalid input")
                
            elif choice == "6":
                self.display_week_schedules(next_week_start, "NEXT WEEK")
                
            elif choice == "7":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice")

def main():
    mirror_system = ScheduleMirror()
    mirror_system.run_mirror_system()

if __name__ == "__main__":
    main()
