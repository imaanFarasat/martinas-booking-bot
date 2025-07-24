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
        """Get MySQL connection with proper transaction support"""
        return mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            autocommit=False,  # Enable proper transaction control
            use_unicode=True,
            charset='utf8mb4'
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
        """Remove a staff member and their schedules with proper transaction handling"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Start transaction
            conn.start_transaction()
            
            # Get staff name before deletion for logging
            cursor.execute('SELECT name FROM staff WHERE id = %s', (staff_id,))
            staff_record = cursor.fetchone()
            
            if not staff_record:
                raise ValueError(f"Staff member with ID {staff_id} not found")
                
            staff_name = staff_record[0]
            
            # Log the staff removal
            cursor.execute('''
                INSERT INTO schedule_changes (staff_id, action, old_data, changed_by)
                VALUES (%s, %s, %s, %s)
            ''', (staff_id, 'REMOVE_STAFF', json.dumps({'name': staff_name}), 'ADMIN'))
            
            # Remove staff (schedules will be removed by CASCADE)
            cursor.execute('DELETE FROM staff WHERE id = %s', (staff_id,))
            
            conn.commit()
            logger.info(f"Staff member '{staff_name}' with ID {staff_id} removed")
            print(f"SUCCESS: Staff member '{staff_name}' removed")
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error removing staff with ID {staff_id}: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            cursor.close()
            conn.close()
    
    def get_all_staff(self):
        """Get all staff members with proper transaction handling"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id, name FROM staff ORDER BY name')
            staff = cursor.fetchall()
            conn.commit()  # Commit the read transaction
            return staff
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error fetching all staff: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            cursor.close()
            conn.close()
    
    def get_staff_by_id(self, staff_id):
        """Get staff member by ID with proper transaction handling"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id, name FROM staff WHERE id = %s', (staff_id,))
            staff = cursor.fetchone()
            conn.commit()  # Commit the read transaction
            return staff
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error fetching staff by ID {staff_id}: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            cursor.close()
            conn.close()
    
    def save_schedule(self, staff_id, day_of_week, is_working, start_time=None, end_time=None, schedule_date=None, changed_by="ADMIN"):
        """Save or update a schedule for a staff member with proper transaction management"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Start explicit transaction
            conn.start_transaction()
            
            # Validate inputs
            if not isinstance(staff_id, int) or staff_id <= 0:
                raise ValueError(f"Invalid staff_id: {staff_id}")
            
            if day_of_week not in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
                raise ValueError(f"Invalid day_of_week: {day_of_week}")
            
            # Validate time formats if working
            if is_working and (start_time or end_time):
                if start_time and not self._validate_time_string(start_time):
                    raise ValueError(f"Invalid start_time format: {start_time}")
                if end_time and not self._validate_time_string(end_time):
                    raise ValueError(f"Invalid end_time format: {end_time}")
            
            # Verify staff exists
            cursor.execute('SELECT id, name FROM staff WHERE id = %s', (staff_id,))
            staff_record = cursor.fetchone()
            if not staff_record:
                raise ValueError(f"Staff member with ID {staff_id} not found")
            
            staff_name = staff_record[1]
            
            # Get existing schedule data for logging
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
            
            # Prepare new data for logging
            new_data = {
                'is_working': bool(is_working),
                'start_time': str(start_time) if start_time else None,
                'end_time': str(end_time) if end_time else None,
                'schedule_date': str(schedule_date) if schedule_date else None
            }
            
            # Check if there's actually a change
            if existing:
                old_data = {
                    'is_working': bool(existing[0]),
                    'start_time': str(existing[1]) if existing[1] else None,
                    'end_time': str(existing[2]) if existing[2] else None,
                    'schedule_date': str(schedule_date) if schedule_date else None
                }
                
                has_changes = (
                    old_data['is_working'] != new_data['is_working'] or
                    old_data['start_time'] != new_data['start_time'] or
                    old_data['end_time'] != new_data['end_time']
                )
                
                if not has_changes:
                    # No changes detected, still return success
                    print(f"DEBUG: No changes detected for {staff_name} ({staff_id}) on {day_of_week}")
                    conn.commit()  # Commit the read transaction
                    return True
                
                action = 'UPDATE_SCHEDULE'
            else:
                old_data = None
                action = 'ADD_SCHEDULE'
            
            # REPLACE INTO ensures the latest save replaces any existing data
            cursor.execute('''
                REPLACE INTO schedules 
                (staff_id, day_of_week, schedule_date, is_working, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (staff_id, day_of_week, schedule_date, is_working, start_time, end_time))
            
            # Log the schedule change
            cursor.execute('''
                INSERT INTO schedule_changes (staff_id, action, day_of_week, old_data, new_data, changed_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (staff_id, action, day_of_week, json.dumps(old_data) if old_data else None, json.dumps(new_data), changed_by))
            
            # Commit the transaction
            conn.commit()
            
            # Log success
            if existing:
                logger.info(f"Schedule updated for '{staff_name}' on {day_of_week}: {start_time}-{end_time}")
                print(f"SUCCESS: Schedule UPDATED for {staff_name} on {day_of_week}: {start_time}-{end_time}")
            else:
                logger.info(f"Schedule added for '{staff_name}' on {day_of_week}: {start_time}-{end_time}")
                print(f"SUCCESS: Schedule ADDED for {staff_name} on {day_of_week}: {start_time}-{end_time}")
            
            return True
            
        except mysql.connector.Error as db_error:
            # MySQL-specific error
            conn.rollback()
            error_msg = f"MySQL error saving schedule for staff_id {staff_id} on {day_of_week}: {db_error}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        except ValueError as val_error:
            # Validation error
            conn.rollback()
            error_msg = f"Validation error saving schedule: {val_error}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        except Exception as e:
            # General error
            conn.rollback()
            error_msg = f"Unexpected error saving schedule for staff_id {staff_id} on {day_of_week}: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            cursor.close()
            conn.close()
    
    def _validate_time_string(self, time_str):
        """Validate time string format (HH:MM)"""
        try:
            if not time_str:
                return True  # Empty is valid for optional times
            
            if not isinstance(time_str, str):
                return False
                
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
                
            hours, minutes = int(parts[0]), int(parts[1])
            return 0 <= hours <= 23 and 0 <= minutes <= 59
            
        except (ValueError, AttributeError):
            return False
    
    def get_staff_schedule(self, staff_id):
        """Get complete schedule for a staff member with proper transaction handling"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            print(f"DEBUG: get_staff_schedule - Fetching schedule for staff_id {staff_id}")
            cursor.execute('''
                SELECT day_of_week, is_working, start_time, end_time 
                FROM schedules 
                WHERE staff_id = %s 
                ORDER BY FIELD(day_of_week, 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
            ''', (staff_id,))
            schedule = cursor.fetchall()
            conn.commit()  # Commit the read transaction
            
            print(f"DEBUG: get_staff_schedule - Found {len(schedule)} schedule entries for staff_id {staff_id}")
            if schedule:
                print(f"DEBUG: get_staff_schedule - Sample: {schedule[:2]}")
            
            return schedule
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error fetching schedule for staff_id {staff_id}: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            cursor.close()
            conn.close()
    
    def get_all_schedules(self):
        """Get all schedules for all staff with proper transaction handling"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            print(f"DEBUG: get_all_schedules - Starting database fetch")
            cursor.execute('''
                SELECT s.name, sch.day_of_week, sch.schedule_date, sch.is_working, sch.start_time, sch.end_time
                FROM staff s
                LEFT JOIN schedules sch ON s.id = sch.staff_id
                ORDER BY s.name, FIELD(sch.day_of_week, 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
            ''')
            schedules = cursor.fetchall()
            conn.commit()  # Commit the read transaction
            
            print(f"DEBUG: get_all_schedules - Fetched {len(schedules)} schedule records")
            if schedules:
                print(f"DEBUG: get_all_schedules - Sample records: {schedules[:3]}")
            
            return schedules
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error fetching all schedules: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            cursor.close()
            conn.close()
    
    def get_staff_with_complete_schedules(self):
        """Get staff who have complete weekly schedules with proper transaction handling"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT s.id, s.name, COUNT(sch.day_of_week) as schedule_count
                FROM staff s
                LEFT JOIN schedules sch ON s.id = sch.staff_id
                GROUP BY s.id, s.name
                HAVING schedule_count = 7
            ''')
            staff_with_schedules = cursor.fetchall()
            conn.commit()  # Commit the read transaction
            return staff_with_schedules
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error fetching staff with complete schedules: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            cursor.close()
            conn.close()
    
    def get_staff_without_complete_schedules(self):
        """Get staff who don't have complete weekly schedules with proper transaction handling"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT s.id, s.name, COUNT(sch.day_of_week) as schedule_count
                FROM staff s
                LEFT JOIN schedules sch ON s.id = sch.staff_id
                GROUP BY s.id, s.name
                HAVING schedule_count < 7
            ''')
            staff_without_schedules = cursor.fetchall()
            conn.commit()  # Commit the read transaction
            return staff_without_schedules
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error fetching staff without complete schedules: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            cursor.close()
            conn.close()
    
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