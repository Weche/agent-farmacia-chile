#!/usr/bin/env python3
"""
Quick test to check Las Condes pharmacies in the database
"""

import sqlite3

def check_las_condes():
    conn = sqlite3.connect('pharmacy_finder.db')
    cursor = conn.cursor()

    print("🔍 Checking Las Condes pharmacies in database...")
    print("=" * 60)

    # First, let's see what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Available tables:", [table[0] for table in tables])

    # Check all Las Condes pharmacies - try different possible table names
    possible_tables = ['farmacias', 'pharmacies', 'pharmacy']
    table_found = None
    
    for table_name in possible_tables:
        try:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            if cursor.fetchone():
                table_found = table_name
                break
        except:
            continue
    
    if not table_found and tables:
        # Use the first table found
        table_found = tables[0][0]
    
    if not table_found:
        print("❌ No suitable table found!")
        conn.close()
        return
        
    print(f"Using table: {table_found}")

    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_found});")
    columns = cursor.fetchall()
    print("Table columns:", [col[1] for col in columns])

    # Check all Las Condes pharmacies
    cursor.execute(f'''
    SELECT *
    FROM {table_found} 
    WHERE UPPER(comuna) = 'LAS CONDES'
    LIMIT 10
    ''')

    results = cursor.fetchall()
    
    print(f"Total Las Condes pharmacies: {len(results)}")
    print("\nSample pharmacies:")
    
    for row in results[:5]:  # Show first 5
        print(f'  {row}')

    conn.close()

if __name__ == "__main__":
    check_las_condes()
