#!/usr/bin/env python3
"""
Production MySQL database cleanup - removes duplicate schedule records
"""
import os
import mysql.connector
from datetime import datetime

def cleanup_production_database():
    """Clean duplicate records from production MySQL database"""
    
    # Get MySQL connection details from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ No DATABASE_URL found - this script is for production MySQL only")
        return
    
    print("🚨 PRODUCTION DATABASE CLEANUP")
    print("=" * 50)
    print(f"Database URL: {database_url[:50]}...")
    
    try:
        # Parse MySQL URL format: mysql://user:password@host:port/database
        if database_url.startswith('mysql://'):
            url_parts = database_url.replace('mysql://', '').split('/')
            auth_host = url_parts[0]
            database_name = url_parts[1] if len(url_parts) > 1 else ''
            
            if '@' in auth_host:
                auth, host_port = auth_host.split('@')
                if ':' in auth:
                    username, password = auth.split(':', 1)
                else:
                    username, password = auth, ''
            else:
                username, password = '', ''
                host_port = auth_host
            
            if ':' in host_port:
                host, port = host_port.split(':')
                port = int(port)
            else:
                host, port = host_port, 3306
        
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            autocommit=False
        )
        
        cursor = conn.cursor()
        
        print(f"✅ Connected to MySQL database: {database_name}")
        
        # Get all staff
        cursor.execute("SELECT id, name FROM staff ORDER BY name")
        staff_list = cursor.fetchall()
        
        if not staff_list:
            print("❌ No staff found")
            return
        
        total_cleaned = 0
        
        for staff_id, staff_name in staff_list:
            print(f"\n👤 Cleaning {staff_name} (ID: {staff_id})")
            
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            for day in days:
                # Get all records for this staff/day - ORDER BY updated_at DESC to keep most recent
                cursor.execute('''
                    SELECT id, schedule_date, is_working, start_time, end_time, updated_at
                    FROM schedules 
                    WHERE staff_id = %s AND day_of_week = %s
                    ORDER BY updated_at DESC
                ''', (staff_id, day))
                
                records = cursor.fetchall()
                
                if len(records) > 1:
                    print(f"  🔍 {day}: Found {len(records)} duplicate records")
                    
                    # Keep the most recent record (first in ORDER BY updated_at DESC)
                    keep_record = records[0]
                    delete_records = records[1:]  # All others to delete
                    
                    print(f"    ✅ Keeping: ID={keep_record[0]}, date={keep_record[1]}, {keep_record[3]}-{keep_record[4]}")
                    
                    # Delete duplicate records
                    for record in delete_records:
                        print(f"    🗑️ Deleting: ID={record[0]}, date={record[1]}, {record[3]}-{record[4]}")
                        cursor.execute('DELETE FROM schedules WHERE id = %s', (record[0],))
                        total_cleaned += 1
                    
                    # Commit after each day to ensure changes are saved
                    conn.commit()
                    
                elif len(records) == 1:
                    record = records[0]
                    print(f"  ✅ {day}: OK (1 record) - {record[3] or 'OFF'}-{record[4] or 'OFF'}")
                else:
                    print(f"  ⚪ {day}: No records")
        
        print(f"\n📊 CLEANUP SUMMARY:")
        print(f"  Total duplicate records deleted: {total_cleaned}")
        print(f"  Database should now be clean!")
        
        cursor.close()
        conn.close()
        
        print("✅ Production database cleanup completed!")
        
    except Exception as e:
        print(f"❌ Error cleaning production database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup_production_database() 