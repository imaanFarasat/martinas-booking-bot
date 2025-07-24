#!/usr/bin/env python3
"""
Quick edit test
"""
from database_factory import get_database_manager

def test_quick_edit():
    """Test quick edit functionality"""
    try:
        print("🔍 Quick Edit Test")
        print("=" * 50)
        
        db = get_database_manager()
        
        # Get staff
        staff_list = db.get_all_staff()
        if not staff_list:
            print("❌ No staff found")
            return
        
        staff_id, staff_name = staff_list[0]
        print(f"👤 Testing with: {staff_name}")
        
        # Test editing a schedule directly
        print("\n✏️ Testing direct schedule edit...")
        
        # Edit Monday schedule
        db.save_schedule(
            staff_id=staff_id,
            day_of_week='Monday',
            is_working=True,
            start_time='10:00',
            end_time='18:00',
            schedule_date='2024-01-01',
            changed_by='TEST_EDIT'
        )
        
        print("✅ Monday schedule updated")
        
        # Check the result
        schedule = db.get_staff_schedule(staff_id)
        for day, is_working, start_time, end_time in schedule:
            if day == 'Monday':
                print(f"📅 {day}: {start_time} - {end_time}")
        
        print("\n" + "=" * 50)
        print("✅ Quick edit test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quick_edit() 