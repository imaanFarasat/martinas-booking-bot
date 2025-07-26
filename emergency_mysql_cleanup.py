#!/usr/bin/env python3
"""
Emergency MySQL cleanup - direct connection to remove duplicates
"""
import mysql.connector
import os
from urllib.parse import urlparse

def parse_database_url(database_url):
    """Parse DATABASE_URL into connection parameters"""
    if not database_url:
        raise ValueError("DATABASE_URL not found")
    
    # Parse URL: mysql://username:password@host:port/database
    parsed = urlparse(database_url)
    
    return {
        'host': parsed.hostname,
        'port': parsed.port or 3306,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path[1:] if parsed.path else ''  # Remove leading /
    }

def cleanup_mysql_duplicates():
    """Clean duplicate records from MySQL database"""
    
    # You need to set your DATABASE_URL environment variable
    # Or replace this with your actual MySQL connection details
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ Set DATABASE_URL environment variable")
        print("Example: export DATABASE_URL='mysql://user:pass@host:port/database'")
        return
    
    try:
        # Parse connection details
        conn_params = parse_database_url(database_url)
        print(f"🔗 Connecting to MySQL: {conn_params['host']}:{conn_params['port']}")
        
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=conn_params['host'],
            port=conn_params['port'],
            user=conn_params['user'],
            password=conn_params['password'],
            database=conn_params['database'],
            autocommit=False
        )
        
        cursor = conn.cursor()
        print("✅ Connected to MySQL successfully")
        
        # Get all staff
        cursor.execute("SELECT id, name FROM staff ORDER BY name")
        staff_list = cursor.fetchall()
        
        print(f"👥 Found {len(staff_list)} staff members")
        
        total_cleaned = 0
        
        for staff_id, staff_name in staff_list:
            print(f"\n👤 Processing {staff_name} (ID: {staff_id})")
            
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            staff_cleaned = 0
            
            for day in days:
                # Get all records for this staff/day combination
                cursor.execute('''
                    SELECT id, schedule_date, is_working, start_time, end_time, updated_at
                    FROM schedules 
                    WHERE staff_id = %s AND day_of_week = %s
                    ORDER BY updated_at DESC
                ''', (staff_id, day))
                
                records = cursor.fetchall()
                
                if len(records) > 1:
                    print(f"  🔍 {day}: {len(records)} records found")
                    
                    # Keep the most recent (first in DESC order)
                    keep_record = records[0]
                    delete_records = records[1:]
                    
                    print(f"    ✅ Keeping: {keep_record[3]}-{keep_record[4]} (ID: {keep_record[0]})")
                    
                    # Delete duplicates
                    for record in delete_records:
                        print(f"    🗑️ Deleting: {record[3]}-{record[4]} (ID: {record[0]})")
                        cursor.execute('DELETE FROM schedules WHERE id = %s', (record[0],))
                        staff_cleaned += 1
                        total_cleaned += 1
                    
                elif len(records) == 1:
                    record = records[0]
                    print(f"  ✅ {day}: Clean - {record[3] or 'OFF'}-{record[4] or 'OFF'}")
                else:
                    print(f"  ⚪ {day}: No records")
            
            if staff_cleaned > 0:
                # Commit changes for this staff member
                conn.commit()
                print(f"  ✅ Cleaned {staff_cleaned} duplicates for {staff_name}")
        
        print(f"\n📊 CLEANUP SUMMARY:")
        print(f"  Total staff processed: {len(staff_list)}")
        print(f"  Total duplicates removed: {total_cleaned}")
        
        cursor.close()
        conn.close()
        
        if total_cleaned > 0:
            print("✅ Database cleanup completed! Restart your bot to see changes.")
        else:
            print("✅ No duplicates found - database is already clean.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚨 EMERGENCY MySQL DUPLICATE CLEANUP")
    print("=" * 50)
    cleanup_mysql_duplicates() 