#!/usr/bin/env python3
"""
Test pharmacy open/closed status
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import PharmacyDatabase

def test_pharmacy_open_status():
    """Test pharmacy open/closed status"""
    print("🧪 Testing pharmacy open/closed status...")
    
    db = PharmacyDatabase()
    
    # Get Villa Alemana pharmacies
    pharmacies = db.find_by_comuna("Villa Alemana", only_open=False)
    print(f"Found {len(pharmacies)} pharmacies in Villa Alemana")
    
    # Check open status for each
    for i, pharmacy in enumerate(pharmacies, 1):
        is_open = db.is_pharmacy_currently_open(pharmacy)
        print(f"{i}. {pharmacy.nombre}")
        print(f"   Hours: {pharmacy.hora_apertura} - {pharmacy.hora_cierre}")
        print(f"   Day: {pharmacy.dia_funcionamiento}")
        print(f"   Is Open: {is_open}")
        print(f"   Es Turno: {pharmacy.es_turno}")
        print()
        
    # Current time info
    from datetime import datetime, timezone
    import pytz
    
    # Convert to Chilean time
    chile_tz = pytz.timezone('America/Santiago')
    now_utc = datetime.now(timezone.utc)
    now_chile = now_utc.astimezone(chile_tz)
    
    print(f"Current time (Chile): {now_chile}")
    print(f"Current day: {now_chile.strftime('%A').lower()}")

if __name__ == "__main__":
    test_pharmacy_open_status()
