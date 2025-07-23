#!/usr/bin/env python3
"""
Local test script for the combined system
"""
import os
import sys
import threading
import time
from flask import Flask

# Set mock environment variables for testing
os.environ['BOT_TOKEN'] = 'mock_admin_token_for_testing'
os.environ['STAFF_BOT_TOKEN'] = 'mock_staff_token_for_testing'
os.environ['ADMIN_IDS'] = '123456789'
os.environ['DATABASE_PATH'] = 'shared_scheduler.db'

def test_web_server():
    """Test the web server without starting bots"""
    print("🧪 Testing web server setup...")
    
    try:
        from web_server import app
        print("✅ Web server imports successfully")
        
        # Test basic routes
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Home route works")
            else:
                print(f"❌ Home route failed: {response.status_code}")
            
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health route works")
            else:
                print(f"❌ Health route failed: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Web server test failed: {e}")
        return False

def test_bot_imports():
    """Test that both bots can be imported"""
    print("\n🧪 Testing bot imports...")
    
    try:
        from staff_bot import StaffBot
        print("✅ Staff bot imports successfully")
        
        # Test staff bot initialization (without running)
        staff_bot = StaffBot()
        print("✅ Staff bot initializes successfully")
        
        return True
    except Exception as e:
        print(f"❌ Staff bot test failed: {e}")
        return False

def test_database_access():
    """Test database access"""
    print("\n🧪 Testing database access...")
    
    try:
        import sqlite3
        
        if not os.path.exists('shared_scheduler.db'):
            print("❌ shared_scheduler.db not found")
            return False
        
        conn = sqlite3.connect('shared_scheduler.db')
        cursor = conn.cursor()
        
        # Test staff table
        cursor.execute('SELECT COUNT(*) FROM staff')
        staff_count = cursor.fetchone()[0]
        print(f"✅ Staff table accessible: {staff_count} staff members")
        
        # Test schedules table
        cursor.execute('SELECT COUNT(*) FROM schedules')
        schedule_count = cursor.fetchone()[0]
        print(f"✅ Schedules table accessible: {schedule_count} schedule entries")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_requirements():
    """Test that all required packages are installed"""
    print("\n🧪 Testing requirements...")
    
    required_packages = [
        ('flask', 'flask'),
        ('telegram', 'telegram'),
        ('pytz', 'pytz'),
        ('reportlab', 'reportlab'),
        ('python-dotenv', 'dotenv')
    ]
    
    all_good = True
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} available")
        except ImportError:
            print(f"❌ {package_name} not available")
            all_good = False
    
    return all_good

def main():
    """Run all local tests"""
    print("🚀 Starting local tests for combined system...\n")
    
    tests = [
        test_requirements,
        test_database_access,
        test_bot_imports,
        test_web_server
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All local tests passed!")
        print("\n📋 Next steps:")
        print("1. Set up real bot tokens from @BotFather")
        print("2. Test with real Telegram bots")
        print("3. Deploy to Render")
        
        # Ask if user wants to test with real tokens
        print("\n🤔 Would you like to test with real bot tokens? (y/n)")
        response = input().lower().strip()
        if response == 'y':
            print("\n📝 Please provide:")
            print("1. Admin bot token (from @BotFather)")
            print("2. Staff bot token (from @BotFather)")
            print("3. Your Telegram user ID (for admin access)")
            print("\nEnter 'skip' to skip this step")
            
            admin_token = input("Admin bot token: ").strip()
            if admin_token.lower() != 'skip':
                staff_token = input("Staff bot token: ").strip()
                user_id = input("Your Telegram user ID: ").strip()
                
                if admin_token and staff_token and user_id:
                    print("\n🔧 Setting up real tokens...")
                    os.environ['BOT_TOKEN'] = admin_token
                    os.environ['STAFF_BOT_TOKEN'] = staff_token
                    os.environ['ADMIN_IDS'] = user_id
                    
                    print("✅ Real tokens set! You can now test the bots.")
                    print("💡 Run: python web_server.py")
                    print("💡 Then test both bots on Telegram!")
    else:
        print("❌ Some tests failed. Please fix the issues above before proceeding.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 