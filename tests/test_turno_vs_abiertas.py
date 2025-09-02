#!/usr/bin/env python3
"""
Test script to verify the distinction between "farmacias de turno" and "farmacias abiertas"
"""

import asyncio
import sys
import os

# Add the project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.agents.tools.farmacia_tools import SearchFarmaciasTool

async def test_turno_vs_abiertas():
    """Test the distinction between turno and open pharmacies"""
    print("🧪 Testing distinction between 'farmacias de turno' vs 'farmacias abiertas'")
    print("=" * 80)
    
    tool = SearchFarmaciasTool()
    
    # Test commune that has no turno pharmacies but has regular ones
    comuna = "Las Condes"
    
    print(f"\n1️⃣ Testing 'farmacias de turno' in {comuna}:")
    print("-" * 50)
    result_turno = await tool.execute(comuna=comuna, turno=True, limite=5)
    
    print(f"Total found: {result_turno['total']}")
    print(f"Message: {result_turno['mensaje']}")
    if 'resumen' in result_turno and 'no_turno_found' in result_turno['resumen']:
        print(f"Regular pharmacies available: {result_turno['resumen'].get('regular_pharmacies_available', 0)}")
        print(f"Suggestion: {result_turno['resumen'].get('suggestion', 'N/A')}")
    
    print(f"\n2️⃣ Testing 'farmacias abiertas' in {comuna}:")
    print("-" * 50)
    result_abiertas = await tool.execute(comuna=comuna, turno=False, limite=5)
    
    print(f"Total found: {result_abiertas['total']}")
    print(f"Message: {result_abiertas['mensaje']}")
    
    if result_abiertas['farmacias']:
        print(f"\nFirst few pharmacies found:")
        for i, farmacia in enumerate(result_abiertas['farmacias'][:3], 1):
            print(f"  {i}. {farmacia['nombre']} - {farmacia['direccion']}")
            print(f"     Turno: {farmacia['turno']}, Abierta: {farmacia['abierta']}")
    
    print(f"\n3️⃣ Testing commune with turno pharmacies (Quilpué):")
    print("-" * 50)
    result_quilpue_turno = await tool.execute(comuna="Quilpué", turno=True, limite=3)
    print(f"Quilpué turno pharmacies found: {result_quilpue_turno['total']}")
    print(f"Message: {result_quilpue_turno['mensaje']}")
    
    result_quilpue_abiertas = await tool.execute(comuna="Quilpué", turno=False, limite=3)
    print(f"Quilpué all open pharmacies found: {result_quilpue_abiertas['total']}")
    print(f"Message: {result_quilpue_abiertas['mensaje']}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_turno_vs_abiertas())
