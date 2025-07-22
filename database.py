import sqlite3
import json
from datetime import datetime, timedelta
from config import DATABASE_PATH

class DatabaseManager:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Staff table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER,
                day_of_week TEXT NOT NULL,
                schedule_date DATE,
                is_working BOOLEAN NOT NULL,
                start_time TEXT,
                end_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff (id),
                UNIQUE(staff_id, day_of_week, schedule_date)
            )
        ''')
        
        # Add date column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE schedules ADD COLUMN schedule_date DATE')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.commit()
        conn.close()
    
    def add_staff(self, name):
        """Add a new staff member"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO staff (name) VALUES (?)', (name,))
            staff_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return staff_id
        except sqlite3.IntegrityError:
            return None  # Name already exists
    
    def remove_staff(self, staff_id):
        """Remove a staff member and their schedules"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Remove schedules first
        cursor.execute('DELETE FROM schedules WHERE staff_id = ?', (staff_id,))
        
        # Remove staff
        cursor.execute('DELETE FROM staff WHERE id = ?', (staff_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_staff(self):
        """Get all staff members"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM staff ORDER BY name')
        staff = cursor.fetchall()
        conn.close()
        return staff
    
    def get_staff_by_id(self, staff_id):
        """Get staff member by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM staff WHERE id = ?', (staff_id,))
        staff = cursor.fetchone()
        conn.close()
        return staff
    
    def save_schedule(self, staff_id, day_of_week, is_working, start_time=None, end_time=None, schedule_date=None):
        """Save or update a schedule for a staff member"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO schedules 
            (staff_id, day_of_week, schedule_date, is_working, start_time, end_time, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (staff_id, day_of_week, schedule_date, is_working, start_time, end_time))
        
        conn.commit()
        conn.close()
    
    def get_staff_schedule(self, staff_id):
        """Get complete schedule for a staff member"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT day_of_week, is_working, start_time, end_time 
            FROM schedules 
            WHERE staff_id = ? 
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, s.name, COUNT(sch.day_of_week) as schedule_count
            FROM staff s
            LEFT JOIN schedules sch ON s.id = sch.staff_id
            GROUP BY s.id, s.name
            HAVING schedule_count = 7
        ''')
        staff_with_schedules = cursor.fetchall()
        conn.close()
        return staff_with_schedules
    
    def get_staff_without_complete_schedules(self):
        """Get staff who don't have complete weekly schedules"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, s.name, COUNT(sch.day_of_week) as schedule_count
            FROM staff s
            LEFT JOIN schedules sch ON s.id = sch.staff_id
            GROUP BY s.id, s.name
            HAVING schedule_count < 7
        ''')
        staff_without_schedules = cursor.fetchall()
        conn.close()
        return staff_without_schedules 
    
    def reset_all_schedules(self):
        """Reset all schedules - clear all schedule data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear all schedules
        cursor.execute('DELETE FROM schedules')
        
        conn.commit()
        conn.close()
        
        return True 

    def get_schedule_history(self):
        """Get all historical schedules grouped by week dates"""
        conn = sqlite3.connect(self.db_path)
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
                date_obj = datetime.strptime(schedule_date, '%Y-%m-%d').date()
                days_since_sunday = date_obj.weekday() + 1  # Monday=0, so Sunday=6, but we want Sunday=0
                if days_since_sunday == 7:
                    days_since_sunday = 0
                week_start = date_obj - timedelta(days=days_since_sunday)
                
                week_key = week_start.strftime('%Y-%m-%d')
                if week_key not in week_schedules:
                    week_schedules[week_key] = {
                        'week_start': week_start,
                        'schedules': []
                    }
        
        # Get full schedule data for each week
        for week_key, week_info in week_schedules.items():
            week_start = week_info['week_start']
            week_end = week_start + timedelta(days=6)
            
            cursor.execute('''
                SELECT s.name, sch.day_of_week, sch.schedule_date, sch.is_working, sch.start_time, sch.end_time
                FROM staff s
                LEFT JOIN schedules sch ON s.id = sch.staff_id
                WHERE sch.schedule_date BETWEEN ? AND ?
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
            ''', (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
            
            week_info['schedules'] = cursor.fetchall()
        
        conn.close()
        return week_schedules 

    def get_staff_schedule_for_week(self, staff_id, week_start):
        """Get a specific staff member's schedule for a week"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        week_end = week_start + timedelta(days=6)
        
        cursor.execute('''
            SELECT day_of_week, schedule_date, is_working, start_time, end_time
            FROM schedules
            WHERE staff_id = ? AND schedule_date BETWEEN ? AND ?
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
        ''', (staff_id, week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
        
        schedules = cursor.fetchall()
        conn.close()
        
        # Convert to dictionary format
        schedule_dict = {}
        for day, schedule_date, is_working, start_time, end_time in schedules:
            schedule_dict[day] = {
                'schedule_date': schedule_date,
                'is_working': is_working,
                'start_time': start_time,
                'end_time': end_time
            }
        
        return schedule_dict
    
    def get_staff_schedule_history(self, staff_id):
        """Get historical schedules for a specific staff member"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT schedule_date, day_of_week
            FROM schedules 
            WHERE staff_id = ? AND schedule_date IS NOT NULL
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
        ''', (staff_id,))
        
        dates = cursor.fetchall()
        
        # Group by week
        week_schedules = {}
        for schedule_date, day_of_week in dates:
            if schedule_date:
                # Find the Sunday of this week
                date_obj = datetime.strptime(schedule_date, '%Y-%m-%d').date()
                days_since_sunday = date_obj.weekday() + 1  # Monday=0, so Sunday=6, but we want Sunday=0
                if days_since_sunday == 7:
                    days_since_sunday = 0
                week_start = date_obj - timedelta(days=days_since_sunday)
                
                week_key = week_start.strftime('%Y-%m-%d')
                if week_key not in week_schedules:
                    week_schedules[week_key] = {
                        'week_start': week_start,
                        'schedules': []
                    }
        
        # Get full schedule data for each week
        for week_key, week_info in week_schedules.items():
            week_start = week_info['week_start']
            week_end = week_start + timedelta(days=6)
            
            cursor.execute('''
                SELECT s.name, sch.day_of_week, sch.schedule_date, sch.is_working, sch.start_time, sch.end_time
                FROM staff s
                LEFT JOIN schedules sch ON s.id = sch.staff_id
                WHERE s.id = ? AND sch.schedule_date BETWEEN ? AND ?
                ORDER BY 
                    CASE sch.day_of_week
                        WHEN 'Sunday' THEN 1
                        WHEN 'Monday' THEN 2
                        WHEN 'Tuesday' THEN 3
                        WHEN 'Wednesday' THEN 4
                        WHEN 'Thursday' THEN 5
                        WHEN 'Friday' THEN 6
                        WHEN 'Saturday' THEN 7
                    END
            ''', (staff_id, week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
            
            week_info['schedules'] = cursor.fetchall()
        
        conn.close()
        return week_schedules 