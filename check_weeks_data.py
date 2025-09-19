#!/usr/bin/env python3
"""
Check schedule data across multiple weeks (3 weeks before and 3 weeks after)
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
import pytz

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_PATH

def check_weeks_data():
    """Check schedule data across multiple weeks"""
    print("🔍 CHECKING SCHEDULE DATA ACROSS MULTIPLE WEEKS")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Calculate current date and week
        toronto_tz = pytz.timezone('America/Toronto')
        today = datetime.now(toronto_tz).date()
        print(f"📅 Today: {today}")
        
        # Calculate 3 weeks before and 3 weeks after
        days_since_sunday = (today.weekday() + 1) % 7
        current_week_start = today - timedelta(days=days_since_sunday)
        if today.weekday() == 6:  # Sunday
            current_week_start = today
        
        print(f"📅 Current week starts: {current_week_start}")
        
        # Calculate week ranges
        weeks = []
        for i in range(-3, 4):  # 3 weeks before, current week, 3 weeks after
            week_start = current_week_start + timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            weeks.append((week_start, week_end, f"Week {i+4}"))
        
        print(f"\n📊 CHECKING {len(weeks)} WEEKS:")
        print("=" * 70)
        
        for week_start, week_end, week_name in weeks:
            print(f"\n📅 {week_name}: {week_start} to {week_end}")
            
            # Count schedules in this week
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM schedules s
                WHERE s.schedule_date >= ? AND s.schedule_date <= ?
            """, (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
            
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"   ✅ {count} schedules found")
                
                # Show sample schedules
                cursor.execute("""
                    SELECT s.staff_id, st.name, s.day_of_week, s.schedule_date, 
                           s.is_working, s.start_time, s.end_time
                    FROM schedules s
                    JOIN staff st ON s.staff_id = st.id
                    WHERE s.schedule_date >= ? AND s.schedule_date <= ?
                    ORDER BY s.schedule_date, st.name
                    LIMIT 5
                """, (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
                
                sample_schedules = cursor.fetchall()
                print("   📝 Sample schedules:")
                for schedule in sample_schedules:
                    staff_name = schedule[1]
                    day = schedule[2]
                    schedule_date = schedule[3]
                    is_working = schedule[4]
                    start_time = schedule[5]
                    end_time = schedule[6]
                    
                    if is_working:
                        time_info = f"{start_time}-{end_time}" if start_time and end_time else "Not Set"
                    else:
                        time_info = "OFF"
                    
                    print(f"      {staff_name} ({day} {schedule_date}): {time_info}")
            else:
                print(f"   ❌ No schedules found")
        
        # Show all unique schedule dates in database
        print(f"\n📊 ALL SCHEDULE DATES IN DATABASE:")
        print("=" * 70)
        
        cursor.execute("""
            SELECT s.schedule_date, COUNT(*) as count
            FROM schedules s
            GROUP BY s.schedule_date
            ORDER BY s.schedule_date DESC
        """)
        
        all_dates = cursor.fetchall()
        
        if all_dates:
            print(f"Found schedules for {len(all_dates)} different dates:")
            for date_info in all_dates:
                date_str = date_info[0]
                count = date_info[1]
                print(f"   {date_str}: {count} schedules")
        else:
            print("No schedule dates found in database")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking weeks data: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔍 MULTI-WEEK SCHEDULE DATA CHECKER")
    print("=" * 70)
    print(f"📅 Current date: {datetime.now().date()}")
    print()
    
    check_weeks_data()
    
    print("\n✅ ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
