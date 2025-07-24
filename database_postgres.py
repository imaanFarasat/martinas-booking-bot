import os
import psycopg2
import json
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL

class PostgreSQLManager:
    def __init__(self):
        self.db_url = DATABASE_URL
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Staff table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id SERIAL PRIMARY KEY,
                staff_id INTEGER REFERENCES staff(id) ON DELETE CASCADE,
                day_of_week VARCHAR(20) NOT NULL,
                schedule_date DATE,
                is_working BOOLEAN NOT NULL,
                start_time TIME,
                end_time TIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(staff_id, day_of_week, schedule_date)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedules_staff_id ON schedules(staff_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedules_day ON schedules(day_of_week)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedules_date ON schedules(schedule_date)')
        
        conn.commit()
        conn.close()
    
    def add_staff(self, name):
        """Add a new staff member"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO staff (name) VALUES (%s) RETURNING id', (name,))
            staff_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()
            return staff_id
        except psycopg2.IntegrityError:
            return None  # Name already exists
    
    def remove_staff(self, staff_id):
        """Remove a staff member and their schedules"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # PostgreSQL will automatically delete schedules due to CASCADE
        cursor.execute('DELETE FROM staff WHERE id = %s', (staff_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_staff(self):
        """Get all staff members"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM staff ORDER BY name')
        staff = cursor.fetchall()
        conn.close()
        return staff
    
    def get_staff_by_id(self, staff_id):
        """Get staff member by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM staff WHERE id = %s', (staff_id,))
        staff = cursor.fetchone()
        conn.close()
        return staff
    
    def save_schedule(self, staff_id, day_of_week, is_working, start_time=None, end_time=None, schedule_date=None):
        """Save or update a schedule for a staff member"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO schedules 
            (staff_id, day_of_week, schedule_date, is_working, start_time, end_time, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (staff_id, day_of_week, schedule_date) 
            DO UPDATE SET 
                is_working = EXCLUDED.is_working,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time,
                updated_at = CURRENT_TIMESTAMP
        ''', (staff_id, day_of_week, schedule_date, is_working, start_time, end_time))
        
        conn.commit()
        conn.close()
    
    def get_staff_schedule(self, staff_id):
        """Get complete schedule for a staff member"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT day_of_week, is_working, start_time, end_time 
            FROM schedules 
            WHERE staff_id = %s 
            ORDER BY 
                CASE day_of_week
                    WHEN 'Sunday' THEN 1
                    WHEN 'Monday' THEN 2
                    WHEN 'Tuesday' THEN 3
                    WHEN 'Wednesday' THEN 4
                    WHEN 'Thursday' THEN 5
                    WHEN 'Friday' THEN 6
                    WHEN 'Saturday' THEN 7
                END
        ''', (staff_id,))
        schedule = cursor.fetchall()
        conn.close()
        return schedule
    
    def get_all_schedules(self):
        """Get all schedules for all staff"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.name, sch.day_of_week, sch.schedule_date, sch.is_working, sch.start_time, sch.end_time
            FROM staff s
            LEFT JOIN schedules sch ON s.id = sch.staff_id
            ORDER BY s.name, 
                CASE sch.day_of_week
                    WHEN 'Sunday' THEN 1
                    WHEN 'Monday' THEN 2
                    WHEN 'Tuesday' THEN 3
                    WHEN 'Wednesday' THEN 4
                    WHEN 'Thursday' THEN 5
                    WHEN 'Friday' THEN 6
                    WHEN 'Saturday' THEN 7
                END
        ''')
        schedules = cursor.fetchall()
        conn.close()
        return schedules
    
    def get_staff_with_complete_schedules(self):
        """Get staff who have complete weekly schedules"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, s.name, COUNT(sch.day_of_week) as schedule_count
            FROM staff s
            LEFT JOIN schedules sch ON s.id = sch.staff_id
            GROUP BY s.id, s.name
            HAVING COUNT(sch.day_of_week) = 7
        ''')
        staff_with_schedules = cursor.fetchall()
        conn.close()
        return staff_with_schedules
    
    def get_staff_without_complete_schedules(self):
        """Get staff who don't have complete weekly schedules"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, s.name, COUNT(sch.day_of_week) as schedule_count
            FROM staff s
            LEFT JOIN schedules sch ON s.id = sch.staff_id
            GROUP BY s.id, s.name
            HAVING COUNT(sch.day_of_week) < 7
        ''')
        staff_without_schedules = cursor.fetchall()
        conn.close()
        return staff_without_schedules
    
    def reset_all_schedules(self):
        """Reset all schedules - clear all schedule data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM schedules')
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_schedule_history(self):
        """Get all historical schedules grouped by week dates"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT schedule_date, day_of_week
            FROM schedules 
            WHERE schedule_date IS NOT NULL
            ORDER BY schedule_date DESC, 
                CASE day_of_week
                    WHEN 'Sunday' THEN 1
                    WHEN 'Monday' THEN 2
                    WHEN 'Tuesday' THEN 3
                    WHEN 'Wednesday' THEN 4
                    WHEN 'Thursday' THEN 5
                    WHEN 'Friday' THEN 6
                    WHEN 'Saturday' THEN 7
                END
        ''')
        dates = cursor.fetchall()
        
        # Group by week
        week_schedules = {}
        for schedule_date, day_of_week in dates:
            if schedule_date:
                # Find the Sunday of this week
                date_obj = schedule_date
                days_since_sunday = date_obj.weekday() + 1
                if days_since_sunday == 7:
                    days_since_sunday = 0
                week_start = date_obj - timedelta(days=days_since_sunday)
                
                week_key = week_start.strftime('%Y-%m-%d')
                if week_key not in week_schedules:
                    week_schedules[week_key] = {
                        'week_start': week_start,
                        'schedules': []
                    }
                
                week_schedules[week_key]['schedules'].append({
                    'date': schedule_date,
                    'day': day_of_week
                })
        
        conn.close()
        return week_schedules
    
    def migrate_from_sqlite(self, sqlite_db_path):
        """Migrate data from SQLite to PostgreSQL"""
        import sqlite3
        
        print("🔄 Starting migration from SQLite to PostgreSQL...")
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to PostgreSQL
        pg_conn = self.get_connection()
        pg_cursor = pg_conn.cursor()
        
        try:
            # Migrate staff
            sqlite_cursor.execute('SELECT id, name FROM staff')
            staff_data = sqlite_cursor.fetchall()
            
            for staff_id, name in staff_data:
                pg_cursor.execute('INSERT INTO staff (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING', (staff_id, name))
            
            print(f"✅ Migrated {len(staff_data)} staff members")
            
            # Migrate schedules
            sqlite_cursor.execute('SELECT staff_id, day_of_week, schedule_date, is_working, start_time, end_time FROM schedules')
            schedule_data = sqlite_cursor.fetchall()
            
            for schedule in schedule_data:
                pg_cursor.execute('''
                    INSERT INTO schedules (staff_id, day_of_week, schedule_date, is_working, start_time, end_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (staff_id, day_of_week, schedule_date) DO NOTHING
                ''', schedule)
            
            print(f"✅ Migrated {len(schedule_data)} schedule entries")
            
            pg_conn.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            pg_conn.rollback()
            print(f"❌ Migration failed: {e}")
            raise
        finally:
            sqlite_conn.close()
            pg_conn.close() 