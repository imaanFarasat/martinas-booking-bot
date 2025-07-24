#!/usr/bin/env python3
"""
Test edit flow debugging
"""
import asyncio
from bot_async import StaffSchedulerBot
from config import ADMIN_IDS

async def test_edit_flow():
    """Test the edit flow"""
    try:
        print("🔍 Testing Edit Flow")
        print("=" * 50)
        
        # Create bot instance
        bot = StaffSchedulerBot()
        
        # Test database connection
        staff_list = bot.db.get_all_staff()
        print(f"📋 Staff count: {len(staff_list)}")
        
        if staff_list:
            staff_id, staff_name = staff_list[0]
            print(f"👤 Testing with: {staff_name} (ID: {staff_id})")
            
            # Get current schedule
            schedule = bot.db.get_staff_schedule(staff_id)
            print(f"📅 Current schedule entries: {len(schedule)}")
            
            for day, is_working, start_time, end_time in schedule:
                print(f"  {day}: {'Working' if is_working else 'Off'} - {start_time} to {end_time}")
            
            # Test editing a specific day
            print("\n✏️ Testing edit functionality...")
            
            # Simulate context data
            context_data = {
                'current_staff_id': staff_id,
                'current_staff_name': staff_name,
                'schedule_data': {}
            }
            
            # Convert database format to context format
            for day, is_working, start_time, end_time in schedule:
                context_data['schedule_data'][day] = {
                    'is_working': bool(is_working),
                    'start_time': start_time or '',
                    'end_time': end_time or '',
                    'date': '2024-01-01'  # Example date
                }
            
            print("✅ Context data prepared")
            print(f"📊 Schedule data keys: {list(context_data['schedule_data'].keys())}")
            
        else:
            print("❌ No staff found")
        
        print("\n" + "=" * 50)
        print("✅ Edit flow test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_edit_flow()) 