#!/usr/bin/env python3
"""
Debug pharmacy open status logic
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import PharmacyDatabase

def debug_open_status():
    """Debug the open status logic"""
    print("🧪 Debugging pharmacy open status logic...")
    
    db = PharmacyDatabase()
    pharmacies = db.find_by_comuna("Villa Alemana", only_open=False)
    
    # Current time info
    now = datetime.now()
    current_time = now.time()
    current_day = now.strftime('%A').lower()  # Friday
    
    print(f"Current time: {current_time}")
    print(f"Current day: {current_day}")
    print()
    
    for pharmacy in pharmacies:
        print(f"🏥 {pharmacy.nombre}")
        print(f"   Hours: {pharmacy.hora_apertura} - {pharmacy.hora_cierre}")
        print(f"   Day in DB: '{pharmacy.dia_funcionamiento}'")
        
        # Debug the day matching logic
        operating_days = pharmacy.dia_funcionamiento.lower() if pharmacy.dia_funcionamiento else ""
        print(f"   Operating days (lower): '{operating_days}'")
        
        # Check day matching logic
        day_match = False
        print(f"   Current day '{current_day}' checks:")
        
        if 'viernes' in operating_days or 'friday' in operating_days:
            day_match = True
            print(f"     ✅ Friday match found!")
        elif 'todos' in operating_days or 'all' in operating_days:
            day_match = True
            print(f"     ✅ All days match found!")
        else:
            print(f"     ❌ No day match found")
            
        # Check the current day logic issue
        print(f"   Current day logic check:")
        if 'viernes' in current_day or 'friday' in operating_days:
            print(f"     Current day condition: 'viernes' in '{current_day}' = {'viernes' in current_day}")
            print(f"     OR 'friday' in '{operating_days}' = {'friday' in operating_days}")
        
        # Actually run the database method
        is_open = db.is_pharmacy_currently_open(pharmacy)
        print(f"   Final result: {is_open}")
        print()

if __name__ == "__main__":
    debug_open_status()
