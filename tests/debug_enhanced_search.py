"""
Simple test to debug the enhanced search tool
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.tools.farmacia_tools import SearchFarmaciasTool, SearchFarmaciasNearbyTool
from app.database import PharmacyDatabase

async def debug_search():
    """Debug search tool functionality"""
    print("=== DEBUGGING ENHANCED SEARCH TOOL ===")
    
    # Test direct database connection
    db = PharmacyDatabase()
    pharmacy_count = db.get_pharmacy_count()
    print(f"Database has {pharmacy_count.get('total', 0)} pharmacies total")
    
    # Test finding by comune to get a sample
    santiago_pharmacies = db.find_by_comuna("SANTIAGO")
    if santiago_pharmacies:
        sample = santiago_pharmacies[0]
        print(f"Sample pharmacy: {sample.nombre} in {sample.comuna}")
    else:
        print("No pharmacies found in SANTIAGO")
    
    # Test search tool
    search_tool = SearchFarmaciasTool()
    
    try:
        # Test with simple query
        print("\n--- Testing simple search ---")
        result = await search_tool.execute(comuna="santiago")
        print(f"Found {len(result.get('farmacias', []))} pharmacies for 'santiago'")
        
        if result.get('farmacias'):
            first = result['farmacias'][0]
            print(f"First result: {first.get('nombre')} - {first.get('comuna')}")
            
            # Check if enhanced features are present
            print(f"Has mapas: {'mapas' in first}")
            print(f"Has horario: {'horario' in first}")
            print(f"Has contacto: {'contacto' in first}")
        
    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with specific commune
    try:
        print("\n--- Testing commune search ---")
        result = await search_tool.execute(comuna="las condes")  
        print(f"Found {len(result.get('farmacias', []))} pharmacies for 'las condes'")
        
    except Exception as e:
        print(f"Commune search error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_search())
