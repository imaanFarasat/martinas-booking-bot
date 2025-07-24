#!/usr/bin/env python3
"""
Debug data source discrepancy
"""
from database_factory import get_database_manager

def debug_data_sources():
    """Compare get_staff_schedule() vs direct database query"""
    try:
        print("🔍 DEBUGGING DATA SOURCE DISCREPANCY")
        print("=" * 60)
        
        db = get_database_manager()
        staff_id = 9  # Ami
        
        print(f"👤 Testing staff_id: {staff_id} (Ami)")
        print("-" * 40)
        
        # METHOD 1: Using the bot's get_staff_schedule() function
        print("📋 METHOD 1: Using db.get_staff_schedule()")
        try:
            bot_data = db.get_staff_schedule(staff_id)
            print(f"   Returns {len(bot_data)} records:")
            for i, record in enumerate(bot_data):
                day, is_working, start_time, end_time = record
                print(f"   {i+1}. {day}: working={is_working}, start={start_time}, end={end_time}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # METHOD 2: Direct database query
        print("📋 METHOD 2: Direct database query")
        try:
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
            
            if hasattr(db, 'get_connection'):
                # MySQL - use FIELD function
                order_clause = "ORDER BY FIELD(day_of_week, 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')"
            else:
                # SQLite - use CASE statement
                order_clause = '''ORDER BY 
                    CASE day_of_week
                        WHEN 'Sunday' THEN 1
                        WHEN 'Monday' THEN 2
                        WHEN 'Tuesday' THEN 3
                        WHEN 'Wednesday' THEN 4
                        WHEN 'Thursday' THEN 5
                        WHEN 'Friday' THEN 6
                        WHEN 'Saturday' THEN 7
                    END'''
            
            cursor.execute(f'''
                SELECT day_of_week, is_working, start_time, end_time 
                FROM schedules 
                WHERE staff_id = {param_style}
                {order_clause}
            ''', (staff_id,))
            
            direct_data = cursor.fetchall()
            print(f"   Returns {len(direct_data)} records:")
            for i, record in enumerate(direct_data):
                day, is_working, start_time, end_time = record
                print(f"   {i+1}. {day}: working={is_working}, start={start_time}, end={end_time}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # METHOD 3: Check if there are multiple database connections
        print("📋 METHOD 3: Checking database configuration")
        print(f"   Database type: {type(db).__name__}")
        print(f"   Has get_connection: {hasattr(db, 'get_connection')}")
        
        if hasattr(db, 'db_path'):
            print(f"   SQLite path: {db.db_path}")
        
        # Check environment variables
        import os
        print(f"   DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
        print(f"   DATABASE_PATH: {os.getenv('DATABASE_PATH', 'Not set')}")
        
        print()
        
        # METHOD 4: Check if get_staff_schedule has any caching or special logic
        print("📋 METHOD 4: Checking get_staff_schedule implementation")
        import inspect
        source = inspect.getsource(db.get_staff_schedule)
        print("   Function source:")
        for i, line in enumerate(source.split('\n')[:10], 1):
            print(f"   {i:2d}: {line}")
        if len(source.split('\n')) > 10:
            print(f"   ... ({len(source.split('\n'))-10} more lines)")
        
    except Exception as e:
        print(f"❌ Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_data_sources() 