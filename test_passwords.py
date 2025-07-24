#!/usr/bin/env python3
"""
Test common MySQL passwords
"""
import mysql.connector

def test_password(password):
    """Test a specific password"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password=password
        )
        print(f"✅ Password works: {password}")
        conn.close()
        return True
    except mysql.connector.Error as e:
        if "Access denied" in str(e):
            print(f"❌ Password failed: {password}")
        else:
            print(f"⚠️ Other error with {password}: {e}")
        return False

def test_common_passwords():
    """Test common MySQL passwords"""
    passwords = [
        'imanFarsat',
        'password',
        '123456',
        'root',
        'admin',
        'mysql',
        '',  # empty password
        'imanfarsat',  # lowercase
        'ImanFarsat',  # different case
        'iman_farsat',  # with underscore
        'iman farsat',  # with space
    ]
    
    print("🔍 Testing common passwords...")
    print("=" * 40)
    
    for password in passwords:
        if test_password(password):
            return password
    
    print("=" * 40)
    print("❌ None of the common passwords worked.")
    print("💡 You may need to reset your MySQL root password.")
    return None

if __name__ == "__main__":
    working_password = test_common_passwords()
    if working_password:
        print(f"\n🎉 Found working password: {working_password}")
    else:
        print("\n💡 Try resetting your MySQL root password.") 