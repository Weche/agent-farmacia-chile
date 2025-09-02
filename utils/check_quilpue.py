#!/usr/bin/env python3
"""
Quick Database Check for Quilpué
Test script to understand the database structure and data
"""
import sqlite3
from datetime import datetime

def check_quilpue_pharmacies():
    """Check Quilpué pharmacies in the database"""
    print("🔍 Checking Quilpué Pharmacies in Database")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('pharmacy_finder.db')
        cursor = conn.cursor()
        
        # Check exact table structure
        cursor.execute("PRAGMA table_info(pharmacies)")
        columns = cursor.fetchall()
        print("\n📊 Table Structure (pharmacies):")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check for Quilpué variations
        print("\n🏢 Checking Comuna variations containing 'quilp':")
        cursor.execute("SELECT DISTINCT comuna FROM pharmacies WHERE LOWER(comuna) LIKE '%quilp%'")
        quilpue_variations = cursor.fetchall()
        
        if quilpue_variations:
            for variation in quilpue_variations:
                print(f"  Found: '{variation[0]}'")
        else:
            print("  No variations found with 'quilp'")
        
        # Check exact count for each variation found
        for variation in quilpue_variations:
            comuna_name = variation[0]
            
            # Total pharmacies
            cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE comuna = ?", (comuna_name,))
            total = cursor.fetchone()[0]
            
            # Turno pharmacies
            cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE comuna = ? AND es_turno = 1", (comuna_name,))
            turno_count = cursor.fetchone()[0]
            
            # Sample pharmacies
            cursor.execute("""
                SELECT nombre, direccion, es_turno, lat, lng 
                FROM pharmacies 
                WHERE comuna = ? 
                LIMIT 5
            """, (comuna_name,))
            samples = cursor.fetchall()
            
            print(f"\n📍 Results for '{comuna_name}':")
            print(f"  Total pharmacies: {total}")
            print(f"  Turno pharmacies: {turno_count}")
            print(f"  Sample pharmacies:")
            
            for pharmacy in samples:
                name, address, es_turno, lat, lng = pharmacy
                turno_status = "🟢 TURNO" if es_turno else "⚪ Regular"
                coords = f"({lat}, {lng})" if lat and lng else "(No coords)"
                print(f"    {name} - {address} {turno_status} {coords}")
        
        # Check similar sounding communes
        print(f"\n🔍 Checking similar communes (starting with 'Q'):")
        cursor.execute("SELECT DISTINCT comuna FROM pharmacies WHERE comuna LIKE 'Q%' ORDER BY comuna")
        q_communes = cursor.fetchall()
        
        for commune in q_communes:
            cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE comuna = ?", (commune[0],))
            count = cursor.fetchone()[0]
            print(f"  {commune[0]}: {count} pharmacies")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_quilpue_pharmacies()
    print(f"\n{'✅ Check completed successfully' if success else '❌ Check failed'}")
