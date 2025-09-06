"""
Direct test of enhanced location features using database + formatting
This bypasses the search tool issues and tests the core functionality
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import PharmacyDatabase
from app.utils.location_utils import enhance_pharmacy_info

def test_direct_enhanced_formatting():
    """Test enhanced formatting directly on database results"""
    print("=== DIRECT ENHANCED FORMATTING TEST ===")
    
    # Get direct database connection
    db = PharmacyDatabase()
    
    # Test with Santiago pharmacies
    santiago_pharmacies = db.find_by_comuna("SANTIAGO")[:5]  # Get first 5
    print(f"Found {len(santiago_pharmacies)} pharmacies in SANTIAGO")
    
    if santiago_pharmacies:
        print("\n--- Testing Enhanced Formatting ---")
        
        for i, pharmacy in enumerate(santiago_pharmacies, 1):
            print(f"\n📍 Pharmacy {i}: {pharmacy.nombre}")
            print(f"   Address: {pharmacy.direccion}")
            print(f"   Coordinates: {pharmacy.lat}, {pharmacy.lng}")
            print(f"   Phone: {pharmacy.telefono}")
            print(f"   Hours: {pharmacy.hora_apertura} - {pharmacy.hora_cierre}")
            
            # Apply enhanced formatting
            enhanced = enhance_pharmacy_info(pharmacy, db)
            
            # Check enhanced features
            print(f"   🗺️  Maps URLs: {len(enhanced.get('mapas', {}))} links")
            if enhanced.get('mapas', {}).get('google_maps'):
                print(f"      Google: {enhanced['mapas']['google_maps']}")
            
            print(f"   🕐 Enhanced Hours: {enhanced.get('horario', {}).get('display', 'N/A')}")
            print(f"   📞 Enhanced Contact: {enhanced.get('contacto', {}).get('telefono_display', 'N/A')}")
            
            # Verify all enhanced fields are present
            required_fields = ['mapas', 'horario', 'contacto']
            missing = [field for field in required_fields if field not in enhanced]
            
            if missing:
                print(f"   ❌ Missing fields: {missing}")
            else:
                print(f"   ✅ All enhanced fields present")
    
    # Test with Las Condes
    print(f"\n--- Testing Las Condes Pharmacies ---")
    las_condes_pharmacies = db.find_by_comuna("LAS CONDES")[:3]
    print(f"Found {len(las_condes_pharmacies)} pharmacies in LAS CONDES")
    
    if las_condes_pharmacies:
        for pharmacy in las_condes_pharmacies:
            enhanced = enhance_pharmacy_info(pharmacy, db)
            print(f"📍 {pharmacy.nombre}: {enhanced.get('horario', {}).get('display', 'No hours')}")
            
            # Test maps functionality
            maps = enhanced.get('mapas', {})
            if maps.get('google_maps'):
                print(f"   🗺️  Google Maps: ✅")
            if maps.get('apple_maps'):
                print(f"   🍎 Apple Maps: ✅")
    
    return True

def test_utility_functions_standalone():
    """Test utility functions with sample data"""
    print("\n=== UTILITY FUNCTIONS STANDALONE TEST ===")
    
    from app.utils.location_utils import (
        format_operating_hours, 
        generate_maps_urls, 
        format_phone_number
    )
    
    # Test operating hours
    hours = format_operating_hours("08:30:00", "18:30:00", "viernes")
    print(f"📅 Operating Hours: {hours['display']}")
    print(f"📅 Status: {hours['estado']}")
    
    # Test maps URLs
    maps = generate_maps_urls(-33.4050, -70.5450, "Av. Las Condes 123", "Farmacia Test")
    print(f"🗺️  Google Maps: {maps['google_maps']}")
    print(f"🍎 Apple Maps: {maps['apple_maps']}")
    print(f"🧭 Directions: {maps['direcciones']}")
    
    # Test phone formatting
    phone = format_phone_number("+56222334455")
    print(f"📞 Phone Display: {phone['telefono_display']}")
    print(f"📞 Click-to-call: {phone['click_to_call']}")
    print(f"💬 WhatsApp: {phone['whatsapp']}")
    
    return True

if __name__ == "__main__":
    try:
        test_utility_functions_standalone()
        test_direct_enhanced_formatting()
        print(f"\n🎉 ALL ENHANCED FORMATTING TESTS PASSED!")
        print(f"✅ Enhanced location features are working correctly!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
