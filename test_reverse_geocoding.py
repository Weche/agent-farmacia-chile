#!/usr/bin/env python3
"""
Test reverse geocoding functionality
"""
import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.geocoding_service import ReverseGeocodingService
from app.agents.tools.farmacia_tools import SearchFarmaciasNearbyTool

async def test_reverse_geocoding():
    """Test reverse geocoding service"""
    print("Testing Reverse Geocoding Service...")
    print("=" * 50)
    
    # Initialize service
    geocoding = ReverseGeocodingService()
    
    # Test coordinates in Chile
    test_coordinates = [
        (-33.0443, -71.3744, "Villa Alemana"),
        (-33.4489, -70.6693, "Santiago Centro"),
        (-33.0153, -71.5494, "Valparaiso"),
        (-34.9817, -71.2381, "Talca"), 
        (-36.8201, -73.0444, "Concepción")
    ]
    
    print("\n1. Testing Local Database Geocoding:")
    for lat, lng, expected in test_coordinates:
        print(f"\n   Testing: {lat}, {lng} (Expected: {expected})")
        
        # Test local geocoding
        result = geocoding._reverse_geocode_local(lat, lng)
        print(f"   Local result: {result.commune} (confidence: {result.confidence:.2f})")
        
        # Test full geocoding (local + API)
        full_result = geocoding.reverse_geocode(lat, lng)
        print(f"   Full result: {full_result.commune} (method: {full_result.method})")
        print(f"   Summary: {geocoding.get_location_summary(full_result)}")
    
    # Test with pharmacy search tool
    print("\n\n2. Testing Integration with Pharmacy Search:")
    tool = SearchFarmaciasNearbyTool()
    
    print("\n   Testing Villa Alemana coordinates with geocoding:")
    result = await tool.execute(
        latitud=-33.0443,
        longitud=-71.3744,
        radio_km=10.0,
        solo_abiertas=False,
        limite=5
    )
    
    if result["success"]:
        data = result["data"]
        ubicacion = data["resumen"]["ubicacion_detectada"]
        print(f"   Detected location: {ubicacion['descripcion']}")
        print(f"   Commune: {ubicacion['comuna']}")
        print(f"   Confidence: {ubicacion['confidence']:.2f}")
        print(f"   Method: {ubicacion['metodo']}")
        print(f"   Message: {data['mensaje']}")
        print(f"   Pharmacies found: {data['total']}")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 50)
    print("Reverse geocoding testing completed!")

if __name__ == "__main__":
    asyncio.run(test_reverse_geocoding())