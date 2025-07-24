#!/usr/bin/env python3
"""
Test MySQL connection with the same settings as the setup script
"""
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Test MySQL connection with current environment variables"""
    try:
        # Get environment variables
        host = os.getenv('MYSQL_HOST', 'localhost')
        port = int(os.getenv('MYSQL_PORT', '3306'))
        user = os.getenv('MYSQL_USER', 'root')
        password = os.getenv('MYSQL_PASSWORD', '')
        database = os.getenv('MYSQL_DATABASE', 'staff_scheduler')
        
        print("🔍 Testing MySQL connection...")
        print(f"Host: {host}")
        print(f"Port: {port}")
        print(f"User: {user}")
        print(f"Password: {'*' * len(password) if password else 'None'}")
        print(f"Database: {database}")
        
        # Test connection without database first
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        
        print("✅ Connected to MySQL server successfully!")
        
        # Test database connection
        conn.close()
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        print("✅ Connected to database successfully!")
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_connection() 