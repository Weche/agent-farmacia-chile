#!/usr/bin/env python3
"""
Direct MINSAL Database Synchronization
Bypasses data_updater to avoid Unicode issues on Windows
"""
import requests
import json
import os
import sys
from datetime import datetime

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.database import PharmacyDatabase, Pharmacy

def sync_with_minsal():
    """Directly synchronize database with MINSAL API"""
    
    print("Starting direct MINSAL database synchronization...")
    print("=" * 50)
    
    # Initialize database
    db = PharmacyDatabase()
    
    # Get current count
    current_stats = db.get_pharmacy_count()
    print(f"Current DB: {current_stats['total']} pharmacies ({current_stats['turno']} turno)")
    
    # Fetch from MINSAL API
    api_urls = [
        "https://midas.minsal.cl/farmacia_v2/WS/getLocalesTurnos.php",  # Turno pharmacies
        "https://midas.minsal.cl/farmacia_v2/WS/getLocales.php"         # Regular pharmacies
    ]
    
    all_pharmacies = []
    
    for i, url in enumerate(api_urls):
        is_turno = i == 0  # First URL is turno pharmacies
        type_name = "turno" if is_turno else "regular"
        
        print(f"\nFetching {type_name} pharmacies from MINSAL...")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"  Found {len(data)} {type_name} pharmacies")
                
                # Convert to Pharmacy objects
                for item in data:
                    try:
                        pharmacy = Pharmacy.from_api_data(item, es_turno=is_turno)
                        all_pharmacies.append(pharmacy)
                    except Exception as e:
                        print(f"  Warning: Error processing pharmacy {item.get('local_id', 'unknown')}: {e}")
                        continue
                        
            else:
                print(f"  Warning: No valid data received for {type_name} pharmacies")
                
        except Exception as e:
            print(f"  Error fetching {type_name} pharmacies: {e}")
            return False
    
    if not all_pharmacies:
        print("No pharmacy data retrieved from MINSAL API")
        return False
    
    print(f"\nTotal pharmacies to sync: {len(all_pharmacies)}")
    
    # Clear existing data and save new data
    print("Clearing existing data...")
    
    # Clear all pharmacies from database
    import sqlite3
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pharmacies")
        conn.commit()
    
    # Save new pharmacies
    print("Saving new pharmacy data...")
    db.save_multiple_pharmacies(all_pharmacies)
    
    # Get final count
    final_stats = db.get_pharmacy_count()
    print(f"\nSynchronization complete!")
    print(f"Final DB: {final_stats['total']} pharmacies ({final_stats['turno']} turno)")
    print(f"Change: {final_stats['total'] - current_stats['total']:+d} total")
    
    return True

if __name__ == "__main__":
    success = sync_with_minsal()
    if success:
        print("\nDatabase successfully synchronized with MINSAL API!")
    else:
        print("\nSynchronization failed!")
        sys.exit(1)