import mysql.connector
import json
import logging
from datetime import datetime, timedelta
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

# Configure logging
logger = logging.getLogger(__name__)

class MySQLDatabaseManager:
    def __init__(self):
        self.host = MYSQL_HOST
        self.port = MYSQL_PORT
        self.user = MYSQL_USER
        self.password = MYSQL_PASSWORD
        self.database = MYSQL_DATABASE
        self.init_database()
    
    def get_connection(self):
        """Get MySQL connection"""
        return mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            autocommit=True
        )
    
    def init_database(self):
        """Initialize database with required tables"""
        # Connect without database first
        conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password
        )
        cursor = conn.cursor()
        
        try:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.fetchall()  # Consume any results
            
            cursor.execute(f"USE {self.database}")
            cursor.fetchall()  # Consume any results
            
            # Staff table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS staff (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.fetchall()  # Consume any results
            
            # Schedules table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedules (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    staff_id INT,
                    day_of_week VARCHAR(20) NOT NULL,
                    schedule_date DATE,
                    is_working BOOLEAN NOT NULL,
                    start_time TIME,
                    end_time TIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (staff_id) REFERENCES staff (id) ON DELETE CASCADE,
                    UNIQUE KEY unique_schedule (staff_id, day_of_week, schedule_date)
                )
            ''')
            cursor.fetchall()  # Consume any results
            
            # Schedule changes log table for tracking modifications
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule_changes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    staff_id INT,
                    action VARCHAR(50) NOT NULL,
                    day_of_week VARCHAR(20),
                    old_data JSON,
                    new_data JSON,
                    changed_by VARCHAR(100),
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (staff_id) REFERENCES staff (id) ON DELETE CASCADE
                )
            ''')
            cursor.fetchall()  # Consume any results
            
            # Create indexes for better performance
            try:
                cursor.execute('CREATE INDEX idx_schedules_staff_id ON schedules(staff_id)')
                cursor.fetchall()  # Consume any results
            except mysql.connector.Error as e:
                if e.errno != 1061:  # Error 1061 = Duplicate key name (index already exists)
                    raise
            
            try:
                cursor.execute('CREATE INDEX idx_schedules_day ON schedules(day_of_week)')
                cursor.fetchall()  # Consume any results
            except mysql.connector.Error as e:
                if e.errno != 1061:  # Error 1061 = Duplicate key name (index already exists)
                    raise
            
            try:
                cursor.execute('CREATE INDEX idx_schedules_date ON schedules(schedule_date)')
                cursor.fetchall()  # Consume any results
            except mysql.connector.Error as e:
                if e.errno != 1061:  # Error 1061 = Duplicate key name (index already exists)
                    raise
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"Error initializing database: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def add_staff(self, name):
        """Add a new staff member"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO staff (name) VALUES (%s)', (name,))
            cursor.fetchall()  # Consume any results
            staff_id = cursor.lastrowid
            
            # Log the staff addition
            cursor.execute('''
                INSERT INTO schedule_changes (staff_id, action, new_data, changed_by)
                VALUES (%s, %s, %s, %s)
            ''', (staff_id, 'ADD_STAFF', json.dumps({'name': name}), 'ADMIN'))
            cursor.fetchall()  # Consume any results
            
            conn.commit()
            logger.info(f"Staff member '{name}' added with ID {staff_id}")
            return staff_id
            
        except mysql.connector.IntegrityError:
            conn.rollback()
            logger.warning(f"Staff member '{name}' already exists")
            return None  # Name already exists
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding staff: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def remove_staff(self, staff_id):
        """Remove a staff member and their schedules"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get staff name before deletion for logging
        cursor.execute('SELECT name FROM staff WHERE id = %s', (staff_id,))
        staff_name = cursor.fetchone()
        staff_name = staff_name[0] if staff_name else "Unknown"
        
        # Log the staff removal
        cursor.execute('''
            INSERT INTO schedule_changes (staff_id, action, old_data, changed_by)
            VALUES (%s, %s, %s, %s)
        ''', (staff_id, 'REMOVE_STAFF', json.dumps({'name': staff_name}), 'ADMIN'))
        
        # Remove staff (schedules will be removed by CASCADE)
        cursor.execute('DELETE FROM staff WHERE id = %s', (staff_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"Staff member '{staff_name}' (ID: {staff_id}) removed")
    
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
    
    def save_schedule(self, staff_id, day_of_week, is_working, start_time=None, end_time=None, schedule_date=None, changed_by="ADMIN"):
        """Save or update a schedule for a staff member"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get existing schedule data for logging (include schedule_date in WHERE clause)
            if schedule_date:
                cursor.execute('''
                    SELECT is_working, start_time, end_time 
                    FROM schedules 
                    WHERE staff_id = %s AND day_of_week = %s AND schedule_date = %s
                ''', (staff_id, day_of_week, schedule_date))
            else:
                cursor.execute('''
                    SELECT is_working, start_time, end_time 
                    FROM schedules 
                    WHERE staff_id = %s AND day_of_week = %s AND schedule_date IS NULL
                ''', (staff_id, day_of_week))
            existing = cursor.fetchone()
            
            # Consume any remaining results
            cursor.fetchall()
            
            # Prepare new data for logging
            new_data = {
                'is_working': is_working,
                'start_time': str(start_time) if start_time else None,
                'end_time': str(end_time) if end_time else None,
                'schedule_date': str(schedule_date) if schedule_date else None
            }
            
            # Log the change with proper old/new data comparison
            if existing:
                old_data = {
                    'is_working': existing[0],
                    'start_time': str(existing[1]) if existing[1] else None,
                    'end_time': str(existing[2]) if existing[2] else None,
                    'schedule_date': str(schedule_date) if schedule_date else None
                }
                action = 'UPDATE_SCHEDULE'
                
                # Check if there's actually a change
                has_changes = (
                    old_data['is_working'] != new_data['is_working'] or
                    old_data['start_time'] != new_data['start_time'] or
                    old_data['end_time'] != new_data['end_time']
                )
                
                if not has_changes:
                    # No changes detected, don't log
                    conn.commit()
                    return True
            else:
                old_data = None
                action = 'ADD_SCHEDULE'
            
            # REPLACE INTO ensures the latest save replaces any existing data
            cursor.execute('''
                REPLACE INTO schedules 
                (staff_id, day_of_week, schedule_date, is_working, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (staff_id, day_of_week, schedule_date, is_working, start_time, end_time))
            
            # Consume any remaining results
            cursor.fetchall()
            
            # Log the schedule change with timestamp
            cursor.execute('''
                INSERT INTO schedule_changes (staff_id, action, day_of_week, old_data, new_data, changed_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (staff_id, action, day_of_week, json.dumps(old_data) if old_data else None, json.dumps(new_data), changed_by))
            
            # Consume any remaining results
            cursor.fetchall()
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"Error saving schedule: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
        
        # Get staff name for logging
        staff_name = self.get_staff_by_id(staff_id)
        staff_name = staff_name[1] if staff_name else "Unknown"
        
        if existing:
            logger.info(f"Schedule updated for '{staff_name}' on {day_of_week}: {start_time}-{end_time}")
        else:
            logger.info(f"Schedule added for '{staff_name}' on {day_of_week}: {start_time}-{end_time}")
        
        return True
    
    def get_staff_schedule(self, staff_id):
        """Get complete schedule for a staff member"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT day_of_week, is_working, start_time, end_time 
            FROM schedules 
            WHERE staff_id = %s 
            ORDER BY FIELD(day_of_week, 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
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
            ORDER BY s.name, FIELD(sch.day_of_week, 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
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
            HAVING schedule_count = 7
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
            HAVING schedule_count < 7
        ''')
        staff_without_schedules = cursor.fetchall()
        conn.close()
        return staff_without_schedules
    
    def get_schedule_changes(self, staff_id=None, limit=50):
        """Get schedule change history with optional staff filter"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if staff_id:
            cursor.execute('''
                SELECT sc.id, s.name, sc.action, sc.day_of_week, 
                       sc.old_data, sc.new_data, sc.changed_by, sc.changed_at
                FROM schedule_changes sc
                LEFT JOIN staff s ON sc.staff_id = s.id
                WHERE sc.staff_id = %s
                ORDER BY sc.changed_at DESC
                LIMIT %s
            ''', (staff_id, limit))
        else:
            cursor.execute('''
                SELECT sc.id, s.name, sc.action, sc.day_of_week, 
                       sc.old_data, sc.new_data, sc.changed_by, sc.changed_at
                FROM schedule_changes sc
                LEFT JOIN staff s ON sc.staff_id = s.id
                ORDER BY sc.changed_at DESC
                LIMIT %s
            ''', (limit,))
        
        changes = cursor.fetchall()
        conn.close()
        return changes
    
    def get_latest_schedule_for_staff(self, staff_id):
        """Get the most recent schedule for a staff member (what's currently active)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT day_of_week, schedule_date, is_working, start_time, end_time, updated_at
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
    
    def get_staff_complete_schedule_status(self):
        """Get status of which staff have complete schedules"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                s.id,
                s.name,
                COUNT(sch.day_of_week) as schedule_count,
                CASE 
                    WHEN COUNT(sch.day_of_week) = 7 THEN 'Complete'
                    WHEN COUNT(sch.day_of_week) > 0 THEN 'Partial'
                    ELSE 'No Schedule'
                END as status
            FROM staff s
            LEFT JOIN schedules sch ON s.id = sch.staff_id
            GROUP BY s.id, s.name
            ORDER BY s.name
        ''')
        status = cursor.fetchall()
        conn.close()
        return status
    
    def get_recent_activity(self, days=7):
        """Get recent activity for dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get recent schedule changes
        cursor.execute('''
            SELECT sc.action, s.name, sc.day_of_week, sc.changed_at
            FROM schedule_changes sc
            LEFT JOIN staff s ON sc.staff_id = s.id
            WHERE sc.changed_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY sc.changed_at DESC
            LIMIT 20
        ''', (days,))
        
        recent_changes = cursor.fetchall()
        conn.close()
        return recent_changes 