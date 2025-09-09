#!/usr/bin/env python3
"""
Test the new intelligent radius expansion feature
"""
import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.agents.tools.farmacia_tools import SearchFarmaciasNearbyTool

async def test_radius_expansion():
    """Test the intelligent radius expansion feature"""
    print("Testing Intelligent Radius Expansion...")
    print("=" * 50)
    
    # Initialize the tool
    tool = SearchFarmaciasNearbyTool()
    
    # Test Case 1: Area with few pharmacies (should expand)
    print("\n1. Testing area with few pharmacies (should expand radius):")
    print("   Coordinates: -35.0000, -71.0000 (rural area)")
    
    result = await tool.execute(
        latitud=-35.0000,
        longitud=-71.0000,
        radio_km=10.0,
        solo_abiertas=False,
        limite=10
    )
    
    if result["success"]:
        data = result["data"]
        resumen = data["resumen"]
        print(f"   Radius inicial: {resumen['radio_inicial']}km")
        print(f"   Radius final: {resumen['radio_km']}km")
        print(f"   Expansion occurred: {resumen['radio_expandido']}")
        print(f"   Search attempts: {resumen['intentos_busqueda']}")
        print(f"   Pharmacies found: {data['total']}")
        print(f"   Message: {data['mensaje']}")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Test Case 2: Area with many pharmacies (Villa Alemana - should not expand)
    print("\n2. Testing area with sufficient pharmacies (should NOT expand):")
    print("   Coordinates: -33.0443, -71.3744 (Villa Alemana)")
    
    result = await tool.execute(
        latitud=-33.0443,
        longitud=-71.3744,
        radio_km=10.0,
        solo_abiertas=False,
        limite=10
    )
    
    if result["success"]:
        data = result["data"]
        resumen = data["resumen"]
        print(f"   Radius inicial: {resumen['radio_inicial']}km")
        print(f"   Radius final: {resumen['radio_km']}km")
        print(f"   Expansion occurred: {resumen['radio_expandido']}")
        print(f"   Search attempts: {resumen['intentos_busqueda']}")
        print(f"   Pharmacies found: {data['total']}")
        print(f"   Message: {data['mensaje']}")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Test Case 3: Custom large radius (should not expand further)
    print("\n3. Testing with custom large radius (should not expand):")
    print("   Coordinates: -33.0443, -71.3744, Radius: 20km")
    
    result = await tool.execute(
        latitud=-33.0443,
        longitud=-71.3744,
        radio_km=20.0,
        solo_abiertas=False,
        limite=10
    )
    
    if result["success"]:
        data = result["data"]
        resumen = data["resumen"]
        print(f"   Radius inicial: {resumen['radio_inicial']}km")
        print(f"   Radius final: {resumen['radio_km']}km")
        print(f"   Expansion occurred: {resumen['radio_expandido']}")
        print(f"   Search attempts: {resumen['intentos_busqueda']}")
        print(f"   Pharmacies found: {data['total']}")
        print(f"   Message: {data['mensaje']}")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 50)
    print("Radius expansion testing completed!")

if __name__ == "__main__":
    asyncio.run(test_radius_expansion())