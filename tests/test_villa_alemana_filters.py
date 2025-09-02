#!/usr/bin/env python3
"""
Test Villa Alemana agent responses without turno filter
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.tools.tool_registry import get_tool_registry

async def test_villa_alemana_filters():
    """Test Villa Alemana pharmacy search with different filters"""
    print("🧪 Testing Villa Alemana pharmacy search filters...")
    
    registry = get_tool_registry()
    
    # Test 1: All pharmacies
    print("\n1️⃣ Testing ALL pharmacies in Villa Alemana:")
    tool_result = await registry.execute_tool("search_farmacias", comuna="Villa Alemana", turno=False)
    print(f"Result: {tool_result}")
    
    if tool_result.get('success'):
        farmacias = tool_result.get('data', {}).get('farmacias', [])
        print(f"Found {len(farmacias)} pharmacies (all)")
        for farmacia in farmacias:
            print(f"  - {farmacia.get('nombre', 'Unknown')} - Open: {farmacia.get('abierta', 'Unknown')}")
    
    # Test 2: Only on-duty pharmacies
    print("\n2️⃣ Testing ONLY ON-DUTY pharmacies in Villa Alemana:")
    tool_result = await registry.execute_tool("search_farmacias", comuna="Villa Alemana", turno=True)
    print(f"Result: {tool_result}")
    
    if tool_result.get('success'):
        farmacias = tool_result.get('data', {}).get('farmacias', [])
        print(f"Found {len(farmacias)} on-duty pharmacies")
        for farmacia in farmacias:
            print(f"  - {farmacia.get('nombre', 'Unknown')} - Open: {farmacia.get('abierta', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(test_villa_alemana_filters())
