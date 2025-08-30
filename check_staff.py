#!/usr/bin/env python3
"""
Quick check for staff in database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_factory import get_database_manager

def check_staff():
    """Check current staff in database"""
    db = get_database_manager()
    all_staff = db.get_all_staff()
    
    print("Current staff in database:")
    for staff_id, name in all_staff:
        print(f"  {staff_id}: {name}")
    
    # Check specifically for Kenza
    kenza_found = any(name == 'Kenza' for _, name in all_staff)
    print(f"\nKenza found: {kenza_found}")

if __name__ == "__main__":
    check_staff()
