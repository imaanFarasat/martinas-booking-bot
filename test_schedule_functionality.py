#!/usr/bin/env python3
"""
Test schedule functionality
"""
from database_factory import get_database_manager

def test_schedule_functionality():
    """Test schedule-related database operations"""
    try:
        db = get_database_manager()
        
        print("🧪 Testing Schedule Functionality")
        print("=" * 50)
        
        # Get all staff
        staff_list = db.get_all_staff()
        print(f"📋 Total staff: {len(staff_list)}")
        
        if not staff_list:
            print("❌ No staff found. Add staff first.")
            return
        
        # Test with first staff member
        staff_id, staff_name = staff_list[0]
        print(f"👤 Testing with: {staff_name} (ID: {staff_id})")
        
        # Check current schedule
        current_schedule = db.get_staff_schedule(staff_id)
        print(f"📅 Current schedule entries: {len(current_schedule)}")
        
        # Test adding a schedule
        print("\n📝 Testing schedule addition...")
        test_schedule = {
            'staff_id': staff_id,
            'day_of_week': 'Monday',
            'is_working': True,
            'start_time': '09:00',
            'end_time': '17:00',
            'schedule_date': '2024-01-01'
        }
        
        db.save_schedule(
            staff_id=test_schedule['staff_id'],
            day_of_week=test_schedule['day_of_week'],
            is_working=test_schedule['is_working'],
            start_time=test_schedule['start_time'],
            end_time=test_schedule['end_time'],
            schedule_date=test_schedule['schedule_date'],
            changed_by="TEST_SCRIPT"
        )
        
        print("✅ Schedule saved successfully")
        
        # Check updated schedule
        updated_schedule = db.get_staff_schedule(staff_id)
        print(f"📅 Updated schedule entries: {len(updated_schedule)}")
        
        # Check recent changes
        print("\n📊 Recent Changes:")
        changes = db.get_schedule_changes(limit=5)
        for change_id, staff_name, action, day_of_week, old_data, new_data, changed_by, changed_at in changes:
            print(f"  {changed_at}: {action} - {staff_name} ({day_of_week or 'N/A'}) by {changed_by}")
        
        # Check staff status
        print("\n📈 Staff Status:")
        status = db.get_staff_complete_schedule_status()
        for staff_id, name, count, status_text in status:
            print(f"  {name}: {status_text} ({count}/7 days)")
        
        print("\n" + "=" * 50)
        print("✅ Schedule functionality test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_schedule_functionality() 