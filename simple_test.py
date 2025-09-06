#!/usr/bin/env python3
"""
Test simplificado para el problema de Salamanca
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def simple_test():
    print("🧪 SIMPLE SALAMANCA TEST")
    print("=" * 50)
    
    try:
        # Test 1: Check if tools work directly
        print("1️⃣ Testing SearchFarmaciasTool directly")
        from app.agents.tools.farmacia_tools import SearchFarmaciasTool
        
        tool = SearchFarmaciasTool()
        result = await tool.execute(comuna="Salamanca", turno=False)
        
        print(f"✅ Direct tool result:")
        print(f"   Total: {result.get('total', 0)}")
        print(f"   Success: {result.get('success', 'N/A')}")
        if result.get('farmacias'):
            print(f"   First pharmacy: {result['farmacias'][0].get('nombre', 'N/A')}")
        
        # Test 2: Check agent
        print(f"\n2️⃣ Testing Spanish Agent")
        from app.agents.spanish_agent import SpanishPharmacyAgent
        
        agent = SpanishPharmacyAgent()
        print("✅ Agent initialized")
        
        # Check tools
        if hasattr(agent, 'tool_registry'):
            tools = list(agent.tool_registry.tools.keys())
            print(f"✅ Available tools: {tools}")
        
        # Test one query
        session_id = await agent.create_session()
        response = await agent.process_message(session_id, "Busca farmacias en Salamanca")
        
        print(f"✅ Agent response:")
        print(f"   Tools used: {response.get('tools_used', [])}")
        print(f"   Success: {response.get('success', False)}")
        
        # Write results to file
        with open("simple_test_results.txt", "w", encoding="utf-8") as f:
            f.write("SIMPLE SALAMANCA TEST RESULTS\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Direct tool total: {result.get('total', 0)}\n")
            f.write(f"Agent tools used: {response.get('tools_used', [])}\n")
            f.write(f"Agent success: {response.get('success', False)}\n")
            
            if result.get('farmacias'):
                f.write(f"Sample pharmacy: {result['farmacias'][0].get('nombre', 'N/A')}\n")
            
            # System prompt check
            if 'search_farmacias' in agent.system_prompt:
                f.write("✅ search_farmacias found in system prompt\n")
            else:
                f.write("❌ search_farmacias NOT found in system prompt\n")
        
        print("💾 Results saved to: simple_test_results.txt")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        with open("simple_test_results.txt", "w", encoding="utf-8") as f:
            f.write(f"ERROR: {e}\n")

if __name__ == "__main__":
    asyncio.run(simple_test())
