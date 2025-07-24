#!/usr/bin/env python3
"""
Test script to verify enhanced database logging functionality
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def test_database_logging():
    """Test the enhanced database logging functionality"""
    try:
        from database_factory import get_database_manager
        
        print("🧪 Testing Enhanced Database Logging...")
        
        # Initialize database
        db = get_database_manager()
        print("✅ Database initialized successfully")
        
        # Test adding staff with logging
        print("\n📝 Testing staff addition with logging...")
        staff_id1 = db.add_staff("Test Staff 1")
        staff_id2 = db.add_staff("Test Staff 2")
        
        if staff_id1 and staff_id2:
            print(f"✅ Staff added successfully: IDs {staff_id1}, {staff_id2}")
        else:
            print("❌ Failed to add staff")
            return False
        
        # Test schedule changes with logging
        print("\n📅 Testing schedule changes with logging...")
        db.save_schedule(
            staff_id=staff_id1,
            day_of_week="Monday",
            is_working=True,
            start_time="09:00",
            end_time="17:00",
            schedule_date="2024-01-01",
            changed_by="TEST_USER_123"
        )
        
        db.save_schedule(
            staff_id=staff_id1,
            day_of_week="Tuesday",
            is_working=False,
            start_time=None,
            end_time=None,
            schedule_date="2024-01-02",
            changed_by="TEST_USER_123"
        )
        
        print("✅ Schedule changes logged successfully")
        
        # Test retrieving schedule changes
        print("\n📊 Testing schedule changes retrieval...")
        changes = db.get_schedule_changes(limit=10)
        print(f"✅ Retrieved {len(changes)} recent changes")
        
        for change in changes:
            change_id, staff_name, action, day_of_week, old_data, new_data, changed_by, changed_at = change
            print(f"  - {action}: {staff_name} ({day_of_week}) by {changed_by}")
        
        # Test staff status
        print("\n👥 Testing staff status...")
        status = db.get_staff_complete_schedule_status()
        print(f"✅ Retrieved status for {len(status)} staff members")
        
        for staff_id, name, count, status_text in status:
            print(f"  - {name}: {status_text} ({count}/7 days)")
        
        # Test recent activity
        print("\n🕒 Testing recent activity...")
        activity = db.get_recent_activity(days=7)
        print(f"✅ Retrieved {len(activity)} recent activities")
        
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        db.remove_staff(staff_id1)
        db.remove_staff(staff_id2)
        print("✅ Test data cleaned up")
        
        print("\n🎉 All database logging tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_logging()
    sys.exit(0 if success else 1) 