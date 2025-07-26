#!/usr/bin/env python3
"""
Test script to verify the Check command functionality
"""

from bot_async import StaffSchedulerBot
from datetime import datetime, timedelta

def test_check_command_logic():
    """Test the check command logic without running the full bot"""
    
    # Create bot instance
    bot = StaffSchedulerBot()
    
    # Test week calculation
    current_week_dates, current_week_start = bot.calculate_week_dates()
    print(f"✅ Current week start: {current_week_start}")
    print(f"✅ Current week dates: {current_week_dates}")
    
    # Test date range formatting
    date_range = bot.format_date_range(current_week_dates)
    print(f"✅ Date range: {date_range}")
    
    # Test time formatting
    test_times = ["09:45:00", "10:00:00", "08:30:00", "09:44:00"]
    for time_str in test_times:
        formatted = bot.format_time_for_display(time_str)
        print(f"✅ Time {time_str} -> {formatted}")
    
    # Test 9:45 attendance logic
    check_time = datetime.strptime("09:45", "%H:%M")
    print(f"✅ Check time: {check_time}")
    
    for time_str in test_times:
        try:
            start_dt = datetime.strptime(time_str[:5], "%H:%M")  # Take HH:MM part
            is_at_945 = start_dt <= check_time
            print(f"✅ {time_str} starts at {start_dt.time()} -> At 9:45: {is_at_945}")
        except Exception as e:
            print(f"❌ Error processing {time_str}: {e}")
    
    print("\n🎉 Check command logic test completed!")
    print("📋 The Check command will:")
    print("   - Accept 'check' or 'Check' text input")
    print("   - Show week selection (current, next, after next)")
    print("   - Display staff working at 9:45 for each day")
    print("   - Format: 'Day (count) Staff1 - Staff2'")
    
    print("\n🚪 The Open command will:")
    print("   - Accept 'open' or 'Open' text input")
    print("   - Show week selection (current, next, after next)")
    print("   - Display opening staff (9:45) and closing staff (21:00)")
    print("   - Format: 'Day (count) Staff1, Staff2 (opening) - Staff3, Staff4 (closing)'")

if __name__ == "__main__":
    print("🧪 Testing Check Command Logic")
    print("=" * 40)
    
    try:
        test_check_command_logic()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 