#!/usr/bin/env python3
"""
Database Factory - Automatically chooses between MySQL, PostgreSQL, and SQLite
"""

from config import USE_MYSQL, USE_POSTGRESQL, USE_SQLITE
import logging

logger = logging.getLogger(__name__)

def get_database_manager():
    """Get the appropriate database manager based on configuration"""
    
    if USE_MYSQL:
        try:
            from database_mysql import MySQLManager
            logger.info("Using MySQL database manager")
            return MySQLManager()
        except ImportError as e:
            logger.error(f"Failed to import MySQL manager: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize MySQL manager: {e}")
            raise
    
    elif USE_POSTGRESQL:
        try:
            from database_postgres import PostgreSQLManager
            logger.info("Using PostgreSQL database manager")
            return PostgreSQLManager()
        except ImportError as e:
            logger.error(f"Failed to import PostgreSQL manager: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL manager: {e}")
            raise
    
    elif USE_SQLITE:
        try:
            from database import DatabaseManager
            logger.info("Using SQLite database manager (fallback)")
            return DatabaseManager()
        except ImportError as e:
            logger.error(f"Failed to import SQLite manager: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize SQLite manager: {e}")
            raise
    
    else:
        logger.error("No database configuration found")
        raise RuntimeError("No database configuration found. Please set up MySQL, PostgreSQL, or SQLite.")

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