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
            try:
                cursor.fetchall()
            except:
                pass
            
            cursor.execute(f"USE {self.database}")
            try:
                cursor.fetchall()
            except:
                pass
            
            # Staff table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS staff (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            try:
                cursor.fetchall()
            except:
                pass
            
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
            try:
                cursor.fetchall()
            except:
                pass
            
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
            try:
                cursor.fetchall()
            except:
                pass
            
            # Create indexes for better performance
            try:
                cursor.execute('CREATE INDEX idx_schedules_staff_id ON schedules(staff_id)')
                try:
                    cursor.fetchall()
                except:
                    pass
            except mysql.connector.Error as e:
                if e.errno != 1061:  # Error 1061 = Duplicate key name (index already exists)
                    raise
            
            try:
                cursor.execute('CREATE INDEX idx_schedules_day ON schedules(day_of_week)')
                try:
                    cursor.fetchall()
                except:
                    pass
            except mysql.connector.Error as e:
                if e.errno != 1061:  # Error 1061 = Duplicate key name (index already exists)
                    raise
            
            try:
                cursor.execute('CREATE INDEX idx_schedules_date ON schedules(schedule_date)')
                try:
                    cursor.fetchall()
                except:
                    pass
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
            # Consume any results from INSERT
            try:
                cursor.fetchall()
            except:
                pass
            staff_id = cursor.lastrowid
            
            # Log the staff addition
            cursor.execute('''
                INSERT INTO schedule_changes (staff_id, action, new_data, changed_by)
                VALUES (%s, %s, %s, %s)
            ''', (staff_id, 'ADD_STAFF', json.dumps({'name': name}), 'ADMIN'))
            # Consume any results from INSERT
            try:
                cursor.fetchall()
            except:
                pass
            
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
            # Get staff name before deletion for logging
            cursor.execute('SELECT name FROM staff WHERE id = %s', (staff_id,))
            staff_record = cursor.fetchone()
            # Consume any remaining results
            try:
                cursor.fetchall()
            except:
                pass
            
            if not staff_record:
                raise ValueError(f"Staff member with ID {staff_id} not found")
                
            staff_name = staff_record[0]
            
            # Log the staff removal
            cursor.execute('''
                INSERT INTO schedule_changes (staff_id, action, old_data, changed_by)
                VALUES (%s, %s, %s, %s)
            ''', (staff_id, 'REMOVE_STAFF', json.dumps({'name': staff_name}), 'ADMIN'))
            # Consume any results from INSERT
            try:
                cursor.fetchall()
            except:
                pass
            
            # Remove staff (schedules will be removed by CASCADE)
            cursor.execute('DELETE FROM staff WHERE id = %s', (staff_id,))
            # Consume any results from DELETE
            try:
                cursor.fetchall()
            except:
                pass
            
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
        """Save or update a schedule for a staff member with proper transaction management and verification"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            print(f"DEBUG: Starting save_schedule for staff_id={staff_id}, day={day_of_week}, working={is_working}, start={start_time}, end={end_time}")
            
            # Explicitly start transaction with proper isolation
            cursor.execute("START TRANSACTION")
            try:
                cursor.fetchall()
            except:
                pass
            
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
            try:
                cursor.fetchall()
            except:
                pass
            
            if not staff_record:
                raise ValueError(f"Staff member with ID {staff_id} not found")
            
            staff_name = staff_record[1]
            print(f"DEBUG: Verified staff exists: {staff_name}")
            
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
            try:
                cursor.fetchall()
            except:
                pass
            
            print(f"DEBUG: Existing data: {existing}")
            
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
                    print(f"DEBUG: No changes detected for {staff_name} ({staff_id}) on {day_of_week}")
                    cursor.execute("COMMIT")
                    try:
                        cursor.fetchall()
                    except:
                        pass
                    return True
                
                action = 'UPDATE_SCHEDULE'
                print(f"DEBUG: Will UPDATE existing schedule")
            else:
                old_data = None
                action = 'ADD_SCHEDULE'
                print(f"DEBUG: Will ADD new schedule")
            
            # Use REPLACE INTO to ensure data is saved
            print(f"DEBUG: Executing REPLACE INTO with data: staff_id={staff_id}, day={day_of_week}, date={schedule_date}, working={is_working}, start={start_time}, end={end_time}")
            cursor.execute('''
                REPLACE INTO schedules 
                (staff_id, day_of_week, schedule_date, is_working, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (staff_id, day_of_week, schedule_date, is_working, start_time, end_time))
            try:
                cursor.fetchall()
            except:
                pass
            print(f"DEBUG: REPLACE INTO executed successfully")
            
            # Log the schedule change
            cursor.execute('''
                INSERT INTO schedule_changes (staff_id, action, day_of_week, old_data, new_data, changed_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (staff_id, action, day_of_week, json.dumps(old_data) if old_data else None, json.dumps(new_data), changed_by))
            try:
                cursor.fetchall()
            except:
                pass
            print(f"DEBUG: Change log inserted")
            
            # Explicitly commit the transaction
            print(f"DEBUG: Committing transaction...")
            cursor.execute("COMMIT")
            try:
                cursor.fetchall()
            except:
                pass
            print(f"DEBUG: Transaction committed successfully")
            
            # VERIFICATION: Read back the data to confirm it was saved
            print(f"DEBUG: Verifying save by reading back data...")
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
            
            verification = cursor.fetchone()
            try:
                cursor.fetchall()
            except:
                pass
            
            if verification:
                saved_working, saved_start, saved_end = verification
                print(f"DEBUG: VERIFICATION SUCCESS - Data in DB: working={saved_working}, start={saved_start}, end={saved_end}")
                
                # Verify the data matches what we intended to save
                if (bool(saved_working) == bool(is_working) and 
                    str(saved_start or '') == str(start_time or '') and 
                    str(saved_end or '') == str(end_time or '')):
                    print(f"SUCCESS: Data verified - save is persistent in database")
                else:
                    print(f"WARNING: Data mismatch after save!")
                    print(f"  Expected: working={is_working}, start={start_time}, end={end_time}")
                    print(f"  Found in DB: working={saved_working}, start={saved_start}, end={saved_end}")
            else:
                print(f"ERROR: VERIFICATION FAILED - No data found after save!")
                raise Exception("Save verification failed - data not found in database")
            
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
            print(f"DEBUG: MySQL error occurred, rolling back...")
            try:
                cursor.execute("ROLLBACK")
                cursor.fetchall()
            except:
                pass
            conn.rollback()
            error_msg = f"MySQL error saving schedule for staff_id {staff_id} on {day_of_week}: {db_error}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        except ValueError as val_error:
            # Validation error
            print(f"DEBUG: Validation error occurred, rolling back...")
            try:
                cursor.execute("ROLLBACK")
                cursor.fetchall()
            except:
                pass
            conn.rollback()
            error_msg = f"Validation error saving schedule: {val_error}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        except Exception as e:
            # General error
            print(f"DEBUG: General error occurred, rolling back...")
            try:
                cursor.execute("ROLLBACK")
                cursor.fetchall()
            except:
                pass
            conn.rollback()
            error_msg = f"Unexpected error saving schedule for staff_id {staff_id} on {day_of_week}: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            cursor.close()
            conn.close()
            print(f"DEBUG: Database connection closed")
    
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
        """Get complete schedule for a staff member with proper transaction handling and fresh data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            print(f"DEBUG: get_staff_schedule - Fetching FRESH schedule for staff_id {staff_id}")
            
            # Ensure we get the most current data by starting a new transaction
            cursor.execute("START TRANSACTION")
            try:
                cursor.fetchall()
            except:
                pass
            
            # Set transaction isolation to read committed data
            cursor.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            try:
                cursor.fetchall()
            except:
                pass
            
            cursor.execute('''
                SELECT day_of_week, is_working, start_time, end_time 
                FROM schedules 
                WHERE staff_id = %s 
                ORDER BY FIELD(day_of_week, 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
            ''', (staff_id,))
            schedule = cursor.fetchall()
            
            # Commit to ensure we read the latest committed data
            cursor.execute("COMMIT")
            try:
                cursor.fetchall()
            except:
                pass
            
            print(f"DEBUG: get_staff_schedule - Found {len(schedule)} schedule entries for staff_id {staff_id}")
            if schedule:
                print(f"DEBUG: get_staff_schedule - Sample data: {schedule[:2]}")
                for day, is_working, start_time, end_time in schedule:
                    print(f"DEBUG:   {day}: working={is_working}, start={start_time}, end={end_time}")
            else:
                print(f"DEBUG: get_staff_schedule - NO SCHEDULE DATA FOUND for staff_id {staff_id}")
            
            return schedule
            
        except Exception as e:
            try:
                cursor.execute("ROLLBACK")
                cursor.fetchall()
            except:
                pass
            conn.rollback()
            error_msg = f"Error fetching schedule for staff_id {staff_id}: {e}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
            
        finally:
            cursor.close()
            conn.close()
    
    def get_all_schedules(self):
        """Get all schedules for all staff with proper transaction handling and fresh data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            print(f"DEBUG: get_all_schedules - Starting FRESH database fetch")
            
            # Ensure we get the most current data
            cursor.execute("START TRANSACTION")
            try:
                cursor.fetchall()
            except:
                pass
            
            # Set transaction isolation to read committed data
            cursor.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            try:
                cursor.fetchall()
            except:
                pass
            
            cursor.execute('''
                SELECT s.name, sch.day_of_week, sch.schedule_date, sch.is_working, sch.start_time, sch.end_time
                FROM staff s
                LEFT JOIN schedules sch ON s.id = sch.staff_id
                ORDER BY s.name, FIELD(sch.day_of_week, 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
            ''')
            schedules = cursor.fetchall()
            
            # Commit to ensure we read the latest committed data
            cursor.execute("COMMIT")
            try:
                cursor.fetchall()
            except:
                pass
            
            print(f"DEBUG: get_all_schedules - Fetched {len(schedules)} schedule records from database")
            if schedules:
                print(f"DEBUG: get_all_schedules - Sample records from DB:")
                for i, record in enumerate(schedules[:5]):  # Show first 5 records
                    staff_name, day, schedule_date, is_working, start_time, end_time = record
                    print(f"DEBUG:   {i+1}. {staff_name} {day}: working={is_working}, start={start_time}, end={end_time}")
            else:
                print(f"DEBUG: get_all_schedules - NO SCHEDULE DATA FOUND in database")
            
            return schedules
            
        except Exception as e:
            try:
                cursor.execute("ROLLBACK")
                cursor.fetchall()
            except:
                pass
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