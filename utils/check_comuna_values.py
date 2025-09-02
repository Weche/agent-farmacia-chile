#!/usr/bin/env python3
"""
Check comuna values in database
"""

import sqlite3
import os

def check_comuna_values():
    """Check actual comuna values in database"""
    db_path = "pharmacy_finder.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Checking comuna values containing 'alemana' or 'Alemana':")
    
    # Check case variations
    queries = [
        "SELECT comuna, COUNT(*) FROM pharmacies WHERE comuna LIKE '%alemana%' GROUP BY comuna;",
        "SELECT comuna, COUNT(*) FROM pharmacies WHERE comuna LIKE '%Alemana%' GROUP BY comuna;",
        "SELECT comuna, COUNT(*) FROM pharmacies WHERE comuna LIKE '%ALEMANA%' GROUP BY comuna;",
        "SELECT DISTINCT comuna FROM pharmacies WHERE comuna LIKE '%alemana%' OR comuna LIKE '%Alemana%' OR comuna LIKE '%ALEMANA%';",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}️⃣ Query: {query}")
        cursor.execute(query)
        results = cursor.fetchall()
        print(f"Results: {results}")
    
    # Check all unique comunas to see what we have
    print("\n🗂️ All unique comunas in database:")
    cursor.execute("SELECT DISTINCT comuna FROM pharmacies ORDER BY comuna;")
    all_comunas = cursor.fetchall()
    print(f"Total unique comunas: {len(all_comunas)}")
    
    # Look for anything with "alemana"
    alemana_comunas = [c[0] for c in all_comunas if 'alemana' in c[0].lower()]
    print(f"Comunas containing 'alemana': {alemana_comunas}")
    
    # Show sample pharmacies from these comunas
    for comuna in alemana_comunas:
        print(f"\n📍 Pharmacies in '{comuna}':")
        cursor.execute("SELECT nombre, direccion FROM pharmacies WHERE comuna = ? LIMIT 3;", (comuna,))
        pharmacies = cursor.fetchall()
        for name, address in pharmacies:
            print(f"  - {name} @ {address}")
    
    conn.close()

if __name__ == "__main__":
    check_comuna_values()
