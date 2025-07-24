#!/usr/bin/env python3
"""
Test adding staff names to verify database functionality
"""
from database_factory import get_database_manager

def test_add_staff():
    """Test adding the staff names mentioned by the user"""
    try:
        db = get_database_manager()
        
        print("🧪 Testing Staff Addition")
        print("=" * 40)
        
        # Test names from the user
        test_names = ["Ami", "Asal", "Bea", "Gee", "Jade"]
        
        print(f"Adding {len(test_names)} staff members...")
        
        added_count = 0
        for name in test_names:
            staff_id = db.add_staff(name)
            if staff_id:
                print(f"✅ Added: {name} (ID: {staff_id})")
                added_count += 1
            else:
                print(f"❌ Failed to add: {name} (might already exist)")
        
        print(f"\n📊 Results: {added_count}/{len(test_names)} staff added successfully")
        
        # Check current staff
        print("\n👥 Current Staff in Database:")
        staff = db.get_all_staff()
        if staff:
            for staff_id, name in staff:
                print(f"  ID: {staff_id}, Name: {name}")
        else:
            print("  No staff members found")
        
        # Check recent changes
        print("\n📊 Recent Changes:")
        changes = db.get_schedule_changes(limit=10)
        if changes:
            for change_id, staff_name, action, day_of_week, old_data, new_data, changed_by, changed_at in changes:
                print(f"  {changed_at}: {action} - {staff_name}")
        else:
            print("  No recent changes found")
        
        print("\n" + "=" * 40)
        print("✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_add_staff() 