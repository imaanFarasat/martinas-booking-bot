#!/usr/bin/env python3
"""
Check database contents
"""
from database_factory import get_database_manager

def check_database():
    """Check all database tables"""
    try:
        db = get_database_manager()
        
        print("🗄️ Checking Database Contents")
        print("=" * 50)
        
        # Check staff
        print("\n👥 STAFF TABLE:")
        staff = db.get_all_staff()
        if staff:
            for staff_id, name in staff:
                print(f"  ID: {staff_id}, Name: {name}")
        else:
            print("  No staff members found")
        
        # Check recent changes
        print("\n📊 RECENT CHANGES:")
        changes = db.get_schedule_changes(limit=10)
        if changes:
            for change_id, staff_name, action, day_of_week, old_data, new_data, changed_by, changed_at in changes:
                print(f"  {changed_at}: {action} - {staff_name} ({day_of_week or 'N/A'}) by {changed_by}")
        else:
            print("  No recent changes found")
        
        # Check staff status
        print("\n📈 STAFF STATUS:")
        status = db.get_staff_complete_schedule_status()
        if status:
            for staff_id, name, count, status_text in status:
                print(f"  {name}: {status_text} ({count}/7 days)")
        else:
            print("  No staff status found")
        
        print("\n" + "=" * 50)
        print("✅ Database check completed!")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database() 