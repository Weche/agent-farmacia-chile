#!/usr/bin/env python3
"""
Debug script to test Villa Alemana pharmacy search
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.database import PharmacyDatabase
from app.core.enhanced_pharmacy_search import EnhancedPharmacyDatabase

def test_villa_alemana_search():
    """Test different ways to search for Villa Alemana pharmacies"""
    print("Testing Villa Alemana pharmacy search...")
    print("=" * 50)
    
    # Initialize database
    db = PharmacyDatabase()
    enhanced_db = EnhancedPharmacyDatabase()
    
    # Test variations of Villa Alemana
    test_queries = [
        "villa alemana",
        "Villa Alemana", 
        "VILLA ALEMANA",
        "villa alemana chile",
        "alemana",
        "vila alemana"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        
        # Test basic search
        try:
            pharmacies_basic = db.find_by_comuna(query)
            print(f"   Basic search: {len(pharmacies_basic)} pharmacies found")
            if pharmacies_basic:
                for i, p in enumerate(pharmacies_basic[:3], 1):
                    print(f"      {i}. {p.nombre} - {p.direccion}")
        except Exception as e:
            print(f"   Basic search error: {e}")
        
        # Test smart search
        try:
            pharmacies_smart, match_result = enhanced_db.smart_find_by_comuna(query)
            print(f"   Smart search: {len(pharmacies_smart)} pharmacies found")
            print(f"   Match result: {match_result.matched_commune} (confidence: {match_result.confidence:.3f})")
            if pharmacies_smart:
                for i, p in enumerate(pharmacies_smart[:3], 1):
                    print(f"      {i}. {p.nombre} - {p.direccion}")
        except Exception as e:
            print(f"   Smart search error: {e}")
    
    # Check what communes are actually in the database
    print(f"\nChecking actual commune names containing 'alemana'...")
    try:
        communes = db.get_all_communes()
        alemana_communes = [c for c in communes if 'alemana' in c.lower()]
        print(f"   Found communes: {alemana_communes}")
    except Exception as e:
        print(f"   Error getting communes: {e}")

if __name__ == "__main__":
    test_villa_alemana_search()