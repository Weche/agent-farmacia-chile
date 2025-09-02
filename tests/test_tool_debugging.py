#!/usr/bin/env python3
"""
Test the exact tool flow with debugging
"""

import sys
import os
import asyncio

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.tools.farmacia_tools import SearchFarmaciasTool

async def test_tool_debugging():
    """Test the exact tool flow with debugging"""
    print("🧪 Testing SearchFarmaciasTool with debugging...")
    
    tool = SearchFarmaciasTool()
    
    # Test the tool directly
    print("\n1️⃣ Testing tool with comuna='Villa Alemana', turno=False:")
    try:
        result = await tool.run(comuna="Villa Alemana", turno=False)
        print(f"Tool result: {result}")
        
        if result.get('success') and result.get('data'):
            farmacias = result['data'].get('farmacias', [])
            print(f"Found {len(farmacias)} pharmacies")
            for farmacia in farmacias[:3]:
                print(f"  - {farmacia.get('nombre', 'Unknown')}")
        else:
            print(f"❌ Tool failed or no data")
            
    except Exception as e:
        print(f"❌ Tool error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with exact database name
    print("\n2️⃣ Testing tool with comuna='VILLA ALEMANA', turno=False:")
    try:
        result = await tool.run(comuna="VILLA ALEMANA", turno=False)
        print(f"Tool result: {result}")
        
        if result.get('success') and result.get('data'):
            farmacias = result['data'].get('farmacias', [])
            print(f"Found {len(farmacias)} pharmacies")
            for farmacia in farmacias[:3]:
                print(f"  - {farmacia.get('nombre', 'Unknown')}")
        else:
            print(f"❌ Tool failed or no data")
            
    except Exception as e:
        print(f"❌ Tool error: {e}")
        import traceback
        traceback.print_exc()

    # Test database method directly
    print("\n3️⃣ Testing database method directly:")
    try:
        db_result = tool.db.find_by_comuna("Villa Alemana", only_open=False)
        print(f"Database method result: {len(db_result)} pharmacies")
        for pharmacy in db_result[:3]:
            print(f"  - {pharmacy.nombre}")
    except Exception as e:
        print(f"❌ Database method error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_debugging())
