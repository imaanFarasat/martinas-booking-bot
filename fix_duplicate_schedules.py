#!/usr/bin/env python3
"""
Emergency fix for duplicate schedule records
"""
from database_factory import get_database_manager
from datetime import datetime

def fix_duplicate_schedules():
    """Fix duplicate schedule records by keeping only the most recent"""
    try:
        print("🚨 EMERGENCY DATABASE CLEANUP")
        print("=" * 50)
        
        db = get_database_manager()
        
        # Get all staff
        staff_list = db.get_all_staff()
        if not staff_list:
            print("❌ No staff found")
            return
        
        for staff_id, staff_name in staff_list:
            print(f"\n👤 Checking {staff_name} (ID: {staff_id})")
            
            # Check for duplicates for each day
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            for day in days:
                # Get all records for this staff/day combination
                # Handle different database types
                if hasattr(db, 'get_connection'):
                    # MySQL database
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    param_style = '%s'
                else:
                    # SQLite database
                    import sqlite3
                    conn = sqlite3.connect(db.db_path)
                    cursor = conn.cursor()
                    param_style = '?'
                
                cursor.execute(f'''
                    SELECT id, schedule_date, is_working, start_time, end_time, updated_at
                    FROM schedules 
                    WHERE staff_id = {param_style} AND day_of_week = {param_style}
                    ORDER BY updated_at DESC
                ''', (staff_id, day))
                
                records = cursor.fetchall()
                
                if len(records) > 1:
                    print(f"  🔍 {day}: Found {len(records)} duplicate records")
                    
                    # Keep the most recent record, delete the rest
                    keep_record = records[0]  # Most recent due to ORDER BY updated_at DESC
                    delete_records = records[1:]  # All others
                    
                    print(f"    ✅ Keeping: ID={keep_record[0]}, date={keep_record[1]}, {keep_record[3]}-{keep_record[4]}")
                    
                    for record in delete_records:
                        print(f"    🗑️ Deleting: ID={record[0]}, date={record[1]}, {record[3]}-{record[4]}")
                        cursor.execute(f'DELETE FROM schedules WHERE id = {param_style}', (record[0],))
                    
                    conn.commit()
                    print(f"    ✅ Cleaned up {len(delete_records)} duplicate records for {day}")
                    
                elif len(records) == 1:
                    record = records[0]
                    print(f"  ✅ {day}: OK (1 record) - {record[3]}-{record[4]}")
                else:
                    print(f"  ⚪ {day}: No records")
                
                cursor.close()
                conn.close()
        
        print("\n" + "=" * 50)
        print("✅ Database cleanup completed!")
        print("🔄 Restart your bot to see the fixes.")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_duplicate_schedules() 