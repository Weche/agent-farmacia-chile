#!/usr/bin/env python3
"""
Quick test for Las Condes pharmacies
"""
import sys
import os
import asyncio

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.agents.tools.farmacia_tools import SearchFarmaciasTool

async def test_las_condes():
    """Test Las Condes specifically"""
    print("🔍 Testing Las Condes Pharmacies")
    print("=" * 40)
    
    search_tool = SearchFarmaciasTool()
    
    # Test 1: All pharmacies in Las Condes
    print("\n1. All pharmacies in Las Condes:")
    result_all = await search_tool.execute(comuna="Las Condes", turno=False)
    print(f"   Total pharmacies: {result_all.get('total', 0)}")
    
    # Test 2: Only turno pharmacies in Las Condes
    print("\n2. Turno pharmacies in Las Condes:")
    result_turno = await search_tool.execute(comuna="Las Condes", turno=True)
    print(f"   Turno pharmacies: {result_turno.get('total', 0)}")
    
    if result_turno.get('total', 0) > 0:
        print("   📍 Turno pharmacies found:")
        for farmacia in result_turno.get('farmacias', [])[:5]:
            print(f"      {farmacia['nombre']} - {farmacia['direccion']}")
    else:
        print("   ⚠️ No turno pharmacies found")
        if 'suggestions' in result_turno:
            print(f"   💡 Suggestions: {result_turno['suggestions']['alternatives']}")
    
    # Test 3: Check the raw data
    print(f"\n3. Raw result structure:")
    print(f"   Keys: {list(result_turno.keys())}")
    if 'mensaje' in result_turno:
        print(f"   Message: {result_turno['mensaje']}")
    if 'error' in result_turno:
        print(f"   Error: {result_turno['error']}")

if __name__ == "__main__":
    asyncio.run(test_las_condes())
