#!/usr/bin/env python3
"""
Test Railway bot database connection
"""
import os
import asyncio
from dotenv import load_dotenv
from database_factory import get_database_manager

load_dotenv()

async def test_railway_bot():
    """Test Railway bot functionality"""
    try:
        print("🚀 Testing Railway Bot Database Connection")
        print("=" * 50)
        
        # Check environment variables
        print("🔍 Environment Variables:")
        mysql_host = os.getenv('MYSQL_HOST', 'NOT_SET')
        mysql_user = os.getenv('MYSQL_USER', 'NOT_SET')
        mysql_database = os.getenv('MYSQL_DATABASE', 'NOT_SET')
        bot_token = os.getenv('BOT_TOKEN', 'NOT_SET')
        
        print(f"MySQL Host: {mysql_host}")
        print(f"MySQL User: {mysql_user}")
        print(f"MySQL Database: {mysql_database}")
        print(f"Bot Token: {bot_token[:10] if bot_token != 'NOT_SET' else 'NOT_SET'}...")
        
        # Test database connection
        print("\n🗄️ Testing Database Connection...")
        db = get_database_manager()
        print("✅ Database manager created")
        
        # Test staff operations
        print("\n👥 Testing Staff Operations...")
        staff_list = db.get_all_staff()
        print(f"📋 Total staff: {len(staff_list)}")
        
        if staff_list:
            print("👤 Current staff:")
            for staff_id, name in staff_list:
                print(f"  {staff_id}: {name}")
        else:
            print("❌ No staff found - database is empty")
            
            # Test adding staff
            print("\n➕ Testing staff addition...")
            test_staff_id = db.add_staff("Test Staff")
            print(f"✅ Added test staff with ID: {test_staff_id}")
            
            # Check again
            staff_list = db.get_all_staff()
            print(f"📋 Staff count after adding: {len(staff_list)}")
        
        print("\n" + "=" * 50)
        print("✅ Railway bot test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_railway_bot()) 