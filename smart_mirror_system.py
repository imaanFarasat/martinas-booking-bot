#!/usr/bin/env python3
"""
Smart Mirror System for Telegram Bot - Handles adding/removing staff intelligently
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

class SmartMirrorSystem:
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
    
    def get_week_staff(self, week_start):
        """Get all staff who have schedules in a specific week"""
        week_end = week_start + timedelta(days=6)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT s.staff_id, st.name
            FROM schedules s
            JOIN staff st ON s.staff_id = st.id
            WHERE s.schedule_date >= ? AND s.schedule_date <= ?
            ORDER BY st.name
        """, (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
        
        staff_list = cursor.fetchall()
        conn.close()
        
        return staff_list
    
    def get_current_staff(self):
        """Get all current staff members"""
        return self.db.get_all_staff()
    
    def get_week_schedules(self, week_start):
        """Get all schedules for a specific week"""
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
    
    def smart_mirror_week(self, source_week_start, target_week_start, week_name):
        """Smart mirror with add/remove staff handling"""
        print(f"\n🔄 SMART MIRRORING {week_name}")
        print("=" * 60)
        print(f"📅 From: {source_week_start} to {source_week_start + timedelta(days=6)}")
        print(f"📅 To: {target_week_start} to {target_week_start + timedelta(days=6)}")
        
        # Get source week staff and schedules
        source_staff = self.get_week_staff(source_week_start)
        source_schedules = self.get_week_schedules(source_week_start)
        
        # Get current staff
        current_staff = self.get_current_staff()
        
        # Create staff mappings
        source_staff_names = {name for _, name in source_staff}
        current_staff_names = {name for _, name in current_staff}
        current_staff_id_map = {name: staff_id for staff_id, name in current_staff}
        
        # Calculate differences
        added_staff = current_staff_names - source_staff_names
        removed_staff = source_staff_names - current_staff_names
        existing_staff = source_staff_names & current_staff_names
        
        print(f"\n📊 STAFF ANALYSIS:")
        print(f"✅ Existing staff: {len(existing_staff)}")
        print(f"➕ Added staff: {len(added_staff)}")
        print(f"❌ Removed staff: {len(removed_staff)}")
        
        if existing_staff:
            print(f"\n👥 Existing staff: {', '.join(sorted(existing_staff))}")
        
        if added_staff:
            print(f"\n➕ Added staff: {', '.join(sorted(added_staff))}")
        
        if removed_staff:
            print(f"\n❌ Removed staff: {', '.join(sorted(removed_staff))}")
        
        # Use direct database connection
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        copied_count = 0
        added_count = 0
        failed_count = 0
        
        try:
            # 1. Copy existing staff schedules
            if source_schedules:
                print(f"\n🔄 Copying existing staff schedules...")
                for schedule in source_schedules:
                    staff_name = schedule[1]
                    day = schedule[2]
                    is_working = schedule[4]
                    start_time = schedule[5]
                    end_time = schedule[6]
                    
                    # Only copy if staff still exists
                    if staff_name in existing_staff:
                        staff_id = current_staff_id_map.get(staff_name)
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
            
            # 2. Add new staff with "Not Set" for all days
            if added_staff:
                print(f"\n➕ Adding new staff with 'Not Set' schedules...")
                for staff_name in added_staff:
                    staff_id = current_staff_id_map.get(staff_name)
                    if not staff_id:
                        print(f"❌ Staff ID not found for {staff_name}")
                        failed_count += 1
                        continue
                    
                    # Add "Not Set" schedule for all days
                    for day in DAYS_OF_WEEK:
                        day_index = DAYS_OF_WEEK.index(day)
                        new_date = target_week_start + timedelta(days=day_index)
                        
                        try:
                            # Insert "Not Set" schedule (is_working=1, but no times)
                            cursor.execute('''
                                INSERT OR REPLACE INTO schedules 
                                (staff_id, day_of_week, schedule_date, is_working, start_time, end_time, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                            ''', (staff_id, day, new_date.strftime('%Y-%m-%d'), 1, '', ''))
                            
                            added_count += 1
                            print(f"➕ {staff_name} - {day} ({new_date}): Not Set")
                            
                        except Exception as e:
                            failed_count += 1
                            print(f"❌ Error adding {staff_name} - {day}: {e}")
            
            # Commit all changes
            conn.commit()
            print(f"\n💾 All changes committed to database")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error during smart mirror operation: {e}")
        finally:
            conn.close()
        
        # Summary
        print(f"\n📊 SMART MIRROR SUMMARY:")
        print(f"✅ Copied existing schedules: {copied_count}")
        print(f"➕ Added new staff schedules: {added_count}")
        print(f"❌ Failed operations: {failed_count}")
        print(f"📅 Total operations: {copied_count + added_count + failed_count}")
        
        if added_staff or removed_staff:
            print(f"\n📋 STAFF CHANGES:")
            if added_staff:
                print(f"➕ Added: {', '.join(sorted(added_staff))}")
            if removed_staff:
                print(f"❌ Removed: {', '.join(sorted(removed_staff))}")
        
        if copied_count > 0 or added_count > 0:
            print(f"\n🎉 SUCCESS! {week_name} smart mirrored to next week!")
            print(f"📅 Next week: {target_week_start} to {target_week_start + timedelta(days=6)}")
        
        return {
            'copied': copied_count,
            'added': added_count,
            'failed': failed_count,
            'added_staff': list(added_staff),
            'removed_staff': list(removed_staff),
            'existing_staff': list(existing_staff)
        }
    
    def get_mirror_summary_text(self, result):
        """Get formatted summary text for Telegram"""
        text = "🔄 *Smart Mirror Summary*\n\n"
        
        text += f"✅ *Copied existing schedules:* {result['copied']}\n"
        text += f"➕ *Added new staff schedules:* {result['added']}\n"
        text += f"❌ *Failed operations:* {result['failed']}\n\n"
        
        if result['added_staff']:
            text += f"➕ *Added staff:* {', '.join(result['added_staff'])}\n"
        
        if result['removed_staff']:
            text += f"❌ *Removed staff:* {', '.join(result['removed_staff'])}\n"
        
        if result['existing_staff']:
            text += f"✅ *Existing staff:* {', '.join(result['existing_staff'])}\n"
        
        return text

def main():
    """Test the smart mirror system"""
    mirror_system = SmartMirrorSystem()
    
    current_week_start = mirror_system.get_current_week_start()
    previous_week_start = mirror_system.get_previous_week_start()
    next_week_start = mirror_system.get_next_week_start()
    
    print("🔄 SMART MIRROR SYSTEM TEST")
    print("=" * 60)
    print(f"📅 Current week: {current_week_start} to {current_week_start + timedelta(days=6)}")
    print(f"📅 Previous week: {previous_week_start} to {previous_week_start + timedelta(days=6)}")
    print(f"📅 Next week: {next_week_start} to {next_week_start + timedelta(days=6)}")
    
    # Test smart mirror
    result = mirror_system.smart_mirror_week(previous_week_start, next_week_start, "PREVIOUS WEEK")
    
    # Show summary
    print(f"\n📱 TELEGRAM SUMMARY:")
    print(mirror_system.get_mirror_summary_text(result))

if __name__ == "__main__":
    main()
