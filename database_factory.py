#!/usr/bin/env python3
"""
Database Factory - Automatically chooses between MySQL, PostgreSQL, and SQLite
"""

from config import USE_MYSQL, USE_POSTGRESQL, USE_SQLITE, MYSQL_HOST, MYSQL_USER, MYSQL_DATABASE

def get_database_manager():
    """
    Factory function to get the appropriate database manager
    Priority: MySQL > PostgreSQL > SQLite
    """
    if USE_MYSQL:
        try:
            from database_mysql import MySQLDatabaseManager
            print(f"🗄️ Using MySQL database: {MYSQL_HOST}/{MYSQL_DATABASE}")
            return MySQLDatabaseManager()
        except ImportError:
            print("⚠️ MySQL dependencies not installed, falling back to PostgreSQL")
            if USE_POSTGRESQL:
                try:
                    from database_postgres import PostgreSQLManager
                    print("🗄️ Using PostgreSQL database")
                    return PostgreSQLManager()
                except ImportError:
                    print("⚠️ PostgreSQL dependencies not installed, falling back to SQLite")
                    from database import DatabaseManager
                    return DatabaseManager()
            else:
                from database import DatabaseManager
                print("🗄️ Using SQLite database")
                return DatabaseManager()
    elif USE_POSTGRESQL:
        try:
            from database_postgres import PostgreSQLManager
            print("🗄️ Using PostgreSQL database")
            return PostgreSQLManager()
        except ImportError:
            print("⚠️ PostgreSQL dependencies not installed, falling back to SQLite")
            from database import DatabaseManager
            return DatabaseManager()
    else:
        from database import DatabaseManager
        print("🗄️ Using SQLite database")
        return DatabaseManager()

def migrate_to_mysql(sqlite_db_path='shared_scheduler.db'):
    """
    Migrate data from SQLite to MySQL
    """
    if not USE_MYSQL:
        print("❌ MySQL configuration not set. Cannot migrate to MySQL.")
        return False
    
    try:
        from database_mysql import MySQLDatabaseManager
        mysql_manager = MySQLDatabaseManager()
        # TODO: Implement migration logic
        print("🔄 Migration to MySQL not yet implemented")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def migrate_to_postgresql(sqlite_db_path='shared_scheduler.db'):
    """
    Migrate data from SQLite to PostgreSQL
    """
    if not USE_POSTGRESQL:
        print("❌ DATABASE_URL not set. Cannot migrate to PostgreSQL.")
        return False
    
    try:
        from database_postgres import PostgreSQLManager
        pg_manager = PostgreSQLManager()
        pg_manager.migrate_from_sqlite(sqlite_db_path)
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    # Test database connection
    db = get_database_manager()
    print(f"✅ Database manager created: {type(db).__name__}")
    
    # Test basic operations
    staff_count = len(db.get_all_staff())
    print(f"✅ Staff count: {staff_count}")
    
    if USE_MYSQL:
        print("🚀 Ready to use MySQL!")
    elif USE_POSTGRESQL:
        print("🚀 Ready to use PostgreSQL!")
    else:
        print("📁 Using SQLite (consider upgrading to MySQL/PostgreSQL for production)") 