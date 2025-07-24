#!/usr/bin/env python3
"""
Test the correct password: imanFarasat
"""
import mysql.connector

def test_correct_password():
    """Test the correct password"""
    try:
        print("🔍 Testing correct password: imanFarasat")
        
        conn = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='imanFarasat',
            database='martina_booking_admin_bot'
        )
        
        print("✅ Password works: imanFarasat")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ MySQL Version: {version[0]}")
        
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Password failed: {e}")
        return False

if __name__ == "__main__":
    test_correct_password() 