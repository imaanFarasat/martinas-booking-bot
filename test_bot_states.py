#!/usr/bin/env python3
"""
Test bot conversation states and handlers
"""
import asyncio
from bot_async import StaffSchedulerBot
from config import ADMIN_IDS

async def test_bot_states():
    """Test bot conversation states"""
    try:
        print("🤖 Testing Bot Conversation States")
        print("=" * 50)
        
        # Create bot instance
        bot = StaffSchedulerBot()
        
        print(f"✅ Bot created successfully")
        print(f"👥 Admin IDs: {ADMIN_IDS}")
        
        # Test admin check
        if ADMIN_IDS:
            test_admin_id = ADMIN_IDS[0]
            is_admin = bot.is_admin(test_admin_id)
            print(f"🔐 Admin check for {test_admin_id}: {is_admin}")
        
        # Test database connection
        staff_list = bot.db.get_all_staff()
        print(f"📋 Staff count: {len(staff_list)}")
        
        if staff_list:
            print("👤 Sample staff:")
            for i, (staff_id, name) in enumerate(staff_list[:3]):
                print(f"  {staff_id}: {name}")
        
        print("\n" + "=" * 50)
        print("✅ Bot state test completed!")
        print("💡 If this works, the issue might be in the conversation flow")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bot_states()) 