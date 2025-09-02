#!/usr/bin/env python3
"""
Test database method directly with debugging
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import PharmacyDatabase

def test_database_directly():
    """Test database method directly"""
    print("🧪 Testing database directly...")
    
    db = PharmacyDatabase()
    
    # Test direct search
    print("\n1️⃣ Testing find_by_comuna with debugging:")
    print(f"Database path: {db.db_path}")
    
    # Check if database file exists
    import sqlite3
    if os.path.exists(db.db_path):
        print(f"✅ Database file exists: {db.db_path}")
        
        # Connect directly and check
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Check table name
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {tables}")
        
        # Check Villa Alemana pharmacies directly
        cursor.execute("SELECT * FROM pharmacies WHERE comuna = 'Villa Alemana';")
        results = cursor.fetchall()
        print(f"Direct SQL results for Villa Alemana: {len(results)} pharmacies")
        
        if results:
            # Get column names
            cursor.execute("PRAGMA table_info(pharmacies);")
            columns = cursor.fetchall()
            print(f"Columns: {[col[1] for col in columns]}")
            
            for i, row in enumerate(results[:3], 1):
                print(f"  {i}. {row}")
        
        conn.close()
    else:
        print(f"❌ Database file does not exist: {db.db_path}")
    
    # Test the actual method
    print("\n2️⃣ Testing find_by_comuna method:")
    try:
        results = db.find_by_comuna("Villa Alemana", only_open=False)
        print(f"Method returned: {len(results)} results")
        
        for i, farmacia in enumerate(results[:3], 1):
            print(f"  {i}. {farmacia}")
            
    except Exception as e:
        print(f"❌ Error in find_by_comuna: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_directly()
