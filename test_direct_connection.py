#!/usr/bin/env python3
"""
Test MySQL connection with direct password
"""
import mysql.connector

def test_direct_connection():
    """Test MySQL connection with direct password"""
    try:
        print("🔍 Testing direct MySQL connection...")
        
        # Direct connection with known password
        conn = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='imanFarsat',
            database='martina_booking_admin_bot'
        )
        
        print("✅ Direct connection successful!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ MySQL Version: {version[0]}")
        
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Direct connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_direct_connection() 