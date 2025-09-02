#!/usr/bin/env python3
"""
Test directo de búsqueda por coordenadas
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import find_nearby_pharmacies

async def test_database_direct():
    """Test directo de la función de base de datos"""
    print("🧪 Testing direct database search...")
    
    # Coordenadas de Villa Alemana
    latitude = -33.0485
    longitude = -71.3700
    radius_km = 5.0
    
    print(f"📍 Searching near: {latitude}, {longitude}")
    print(f"🔍 Radius: {radius_km} km")
    
    try:
        result = await find_nearby_pharmacies(latitude, longitude, radius_km)
        
        print(f"✅ Database search completed")
        print(f"📊 Results: {len(result)} pharmacies found")
        
        if result:
            print("\n🏥 First 5 pharmacies:")
            for i, farmacia in enumerate(result[:5], 1):
                print(f"  {i}. {farmacia.get('nombre', 'Unknown')}")
                print(f"     📍 {farmacia.get('comuna', 'Unknown')} - {farmacia.get('direccion', 'Unknown')}")
                if 'distance_km' in farmacia:
                    print(f"     📏 Distance: {farmacia['distance_km']:.2f} km")
        else:
            print("❌ No pharmacies found in the area")
            
    except Exception as e:
        print(f"❌ Error in database search: {e}")
        import traceback
        traceback.print_exc()

async def test_tool_direct():
    """Test directo de la herramienta"""
    print("\n🔧 Testing tool execution...")
    
    try:
        from app.agents.tools.tool_registry import get_tool_registry
        
        registry = get_tool_registry()
        
        # Test coordinates search
        result = await registry.execute_tool(
            "search_farmacias_nearby",
            latitude=-33.0485,
            longitude=-71.3700,
            radius_km=5.0
        )
        
        print(f"✅ Tool execution completed")
        print(f"📊 Success: {result.get('success', False)}")
        
        if result.get('success'):
            data = result.get('data', {})
            farmacias = data.get('farmacias', [])
            print(f"📋 Found {len(farmacias)} pharmacies")
            
            if farmacias:
                print("\n🏥 First 3 pharmacies from tool:")
                for i, farmacia in enumerate(farmacias[:3], 1):
                    print(f"  {i}. {farmacia.get('nombre', 'Unknown')}")
                    print(f"     📍 {farmacia.get('direccion', 'Unknown')}")
        else:
            print(f"❌ Tool execution failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error in tool execution: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("🔍 Testing Coordinates Search - Direct Functions")
    print("=" * 60)
    
    # Test 1: Direct database function
    await test_database_direct()
    
    # Test 2: Direct tool execution
    await test_tool_direct()
    
    print("\n🏁 Tests completed")

if __name__ == "__main__":
    asyncio.run(main())
