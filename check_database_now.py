#!/usr/bin/env python3
"""
Check current database state to find duplicate records
"""
from database_factory import get_database_manager

def check_database_state():
    """Check current database for duplicates"""
    try:
        print("🔍 CHECKING CURRENT DATABASE STATE")
        print("=" * 60)
        
        db = get_database_manager()
        
        # Check Ami specifically (ID 9) since that's what the user is testing
        staff_id = 9
        staff_name = "Ami"
        
        print(f"\n👤 Checking {staff_name} (ID: {staff_id}) - DETAILED ANALYSIS")
        print("-" * 40)
        
        # Get database connection
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
        
        # Get ALL records for this staff member, especially Saturday
        cursor.execute(f'''
            SELECT id, day_of_week, schedule_date, is_working, start_time, end_time, updated_at
            FROM schedules 
            WHERE staff_id = {param_style}
            ORDER BY day_of_week, updated_at DESC
        ''', (staff_id,))
        
        all_records = cursor.fetchall()
        
        print(f"📊 TOTAL RECORDS FOUND: {len(all_records)}")
        print()
        
        # Group by day to find duplicates
        day_records = {}
        for record in all_records:
            day = record[1]  # day_of_week
            if day not in day_records:
                day_records[day] = []
            day_records[day].append(record)
        
        # Check each day
        total_duplicates = 0
        for day in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            records = day_records.get(day, [])
            
            if len(records) == 0:
                print(f"  ⚪ {day}: No records")
            elif len(records) == 1:
                record = records[0]
                print(f"  ✅ {day}: 1 record - {record[4]}-{record[5]} (ID: {record[0]}, Date: {record[2]})")
            else:
                print(f"  🚨 {day}: {len(records)} DUPLICATE RECORDS!")
                total_duplicates += len(records) - 1
                for i, record in enumerate(records):
                    status = "LATEST" if i == 0 else f"OLD #{i}"
                    print(f"     {status}: ID={record[0]}, Date={record[2]}, Times={record[4]}-{record[5]}, Updated={record[6]}")
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total Records: {len(all_records)}")
        print(f"  Expected Records: 7 (one per day)")
        print(f"  Duplicate Records: {total_duplicates}")
        
        if total_duplicates > 0:
            print(f"\n🚨 CRITICAL: Found {total_duplicates} duplicate records!")
            print("This explains the random behavior you're seeing.")
        else:
            print(f"\n✅ Database appears clean for {staff_name}")
        
        cursor.close()
        conn.close()
        
        # Also check the constraints
        print(f"\n🔧 CHECKING DATABASE CONSTRAINTS:")
        print("-" * 40)
        
        if hasattr(db, 'get_connection'):
            # MySQL database
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SHOW CREATE TABLE schedules")
            table_def = cursor.fetchone()
            print("Table Definition:")
            print(table_def[1])
            
            cursor.close()
            conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_state() 