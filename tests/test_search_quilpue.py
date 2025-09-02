#!/usr/bin/env python3
"""
Test the exact search behavior
"""
import sqlite3

def test_search():
    """Test the exact search behavior with different variations"""
    print("🔍 Testing Search Behavior")
    print("=" * 40)
    
    conn = sqlite3.connect('pharmacy_finder.db')
    cursor = conn.cursor()
    
    # Test different variations of Quilpué
    test_cases = [
        "Quilpué",     # With accent (what user/AI likely uses)
        "Quilpue",     # Without accent, proper case
        "QUILPUE",     # Without accent, uppercase (what's in DB)
        "quilpué",     # With accent, lowercase
        "quilpue",     # Without accent, lowercase
    ]
    
    print("Testing direct LIKE matches:")
    for test_comuna in test_cases:
        query = '''
            SELECT COUNT(*) FROM pharmacies
            WHERE LOWER(comuna) LIKE LOWER(?)
        '''
        cursor.execute(query, [f'%{test_comuna}%'])
        count = cursor.fetchone()[0]
        print(f"  '{test_comuna}' -> {count} matches")
    
    print(f"\nTesting with turno filter:")
    for test_comuna in test_cases:
        query = '''
            SELECT COUNT(*) FROM pharmacies
            WHERE LOWER(comuna) LIKE LOWER(?)
              AND es_turno = 1
        '''
        cursor.execute(query, [f'%{test_comuna}%'])
        count = cursor.fetchone()[0]
        print(f"  '{test_comuna}' turno -> {count} matches")
    
    print(f"\nTesting exact matches:")
    cursor.execute("SELECT DISTINCT comuna FROM pharmacies WHERE LOWER(comuna) LIKE '%quilp%'")
    variations_in_db = cursor.fetchall()
    print(f"Actual variations in DB: {[v[0] for v in variations_in_db]}")
    
    conn.close()

if __name__ == "__main__":
    test_search()
