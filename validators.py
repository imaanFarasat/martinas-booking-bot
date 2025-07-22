import re
from datetime import datetime
from config import MIN_START_TIME, MAX_END_TIME

class ScheduleValidator:
    @staticmethod
    def validate_time_format(time_str):
        """
        Validate time format HH:mm or H:mm
        Returns: (is_valid, error_message)
        """
        if not time_str:
            return False, "Time cannot be empty"
        
        # Check format HH:mm or H:mm (more flexible)
        pattern = r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(pattern, time_str):
            return False, "Time must be in HH:MM format (e.g., 12:10, 4:09, 09:45)"
        
        # Parse hours and minutes
        try:
            hours, minutes = map(int, time_str.split(':'))
            if hours < 0 or hours > 23:
                return False, "Hours must be between 0 and 23"
            if minutes < 0 or minutes > 59:
                return False, "Minutes must be between 0 and 59"
        except ValueError:
            return False, "Invalid time format. Use HH:MM (e.g., 12:10, 4:09)"
        
        return True, ""
    
    @staticmethod
    def validate_time_range(start_time, end_time):
        """
        Validate that times are within allowed range and end > start
        Returns: (is_valid, error_message)
        """
        # Validate start time
        start_valid, start_error = ScheduleValidator.validate_time_format(start_time)
        if not start_valid:
            return False, f"Start time: {start_error}"
        
        # Validate end time
        end_valid, end_error = ScheduleValidator.validate_time_format(end_time)
        if not end_valid:
            return False, f"End time: {end_error}"
        
        # Check time range constraints
        if start_time < MIN_START_TIME:
            return False, f"Start time must be {MIN_START_TIME} or later"
        
        if end_time > MAX_END_TIME:
            return False, f"End time must be {MAX_END_TIME} or earlier"
        
        # Check that end time is after start time
        if start_time >= end_time:
            return False, "End time must be after start time"
        
        return True, ""
    
    @staticmethod
    def validate_staff_name(name):
        """
        Validate staff name
        Returns: (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Staff name cannot be empty"
        
        if len(name.strip()) < 2:
            return False, "Staff name must be at least 2 characters long"
        
        if len(name.strip()) > 50:
            return False, "Staff name must be 50 characters or less"
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        pattern = r'^[a-zA-Z\s\-\']+$'
        if not re.match(pattern, name.strip()):
            return False, "Staff name can only contain letters, spaces, hyphens, and apostrophes"
        
        return True, ""
    
    @staticmethod
    def validate_day_of_week(day):
        """
        Validate day of week
        Returns: (is_valid, error_message)
        """
        valid_days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        if day not in valid_days:
            return False, f"Invalid day. Must be one of: {', '.join(valid_days)}"
        
        return True, ""
    
    @staticmethod
    def validate_schedule_data(schedule_data):
        """
        Validate complete schedule data for a staff member
        Returns: (is_valid, error_messages)
        """
        errors = []
        
        for day, data in schedule_data.items():
            # Validate day
            day_valid, day_error = ScheduleValidator.validate_day_of_week(day)
            if not day_valid:
                errors.append(f"{day}: {day_error}")
                continue
            
            # Check if data has required fields
            if 'is_working' not in data:
                errors.append(f"{day}: Missing working status")
                continue
            
            is_working = data['is_working']
            
            if is_working:
                # If working, validate times
                if 'start_time' not in data or 'end_time' not in data:
                    errors.append(f"{day}: Missing start or end time for working day")
                    continue
                
                time_valid, time_error = ScheduleValidator.validate_time_range(
                    data['start_time'], data['end_time']
                )
                if not time_valid:
                    errors.append(f"{day}: {time_error}")
            else:
                # If not working, times should be None or empty
                if data.get('start_time') or data.get('end_time'):
                    errors.append(f"{day}: Should not have times when marked as Off")
        
        return len(errors) == 0, errors 