#!/usr/bin/env python3
"""
Test específico para Las Condes - reproducir el problema exacto
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_las_condes():
    print("🧪 TESTING LAS CONDES ISSUE")
    print("=" * 50)
    
    try:
        # Test 1: Direct tool test
        print("1️⃣ Testing SearchFarmaciasTool directly with 'Las Condes'")
        from app.agents.tools.farmacia_tools import SearchFarmaciasTool
        
        tool = SearchFarmaciasTool()
        result = await tool.execute(comuna="Las Condes", turno=False)
        
        print(f"✅ Direct tool result:")
        print(f"   Total: {result.get('total', 0)}")
        print(f"   Success: {result.get('success', 'N/A')}")
        if result.get('farmacias'):
            print(f"   First pharmacy: {result['farmacias'][0].get('nombre', 'N/A')}")
        
        # Test 2: Test GetCommunesTool
        print(f"\n2️⃣ Testing GetCommunesTool with Región Metropolitana")
        from app.agents.tools.farmacia_tools import GetCommunesTool
        
        commune_tool = GetCommunesTool()
        commune_result = await commune_tool.execute(region="Metropolitana")
        
        print(f"✅ Get communes result:")
        print(f"   Total communes: {len(commune_result.get('communes', []))}")
        print(f"   Success: {commune_result.get('success', 'N/A')}")
        
        # Check if Las Condes is in the list
        communes = commune_result.get('communes', [])
        las_condes_found = any('condes' in commune.lower() for commune in communes)
        print(f"   Las Condes found: {las_condes_found}")
        if communes:
            print(f"   Sample communes: {communes[:5]}")
        
        # Test 3: Agent test
        print(f"\n3️⃣ Testing Spanish Agent with 'Las Condes'")
        from app.agents.spanish_agent import SpanishPharmacyAgent
        
        agent = SpanishPharmacyAgent()
        session_id = await agent.create_session()
        
        # Test the exact query that fails
        response = await agent.process_message(session_id, "dame una lista de farmacias en las condes")
        
        print(f"✅ Agent response:")
        print(f"   Tools used: {response.get('tools_used', [])}")
        print(f"   Success: {response.get('success', False)}")
        print(f"   Response preview: {response.get('response', '')[:200]}...")
        
        # Check tool results
        tool_results = response.get('tool_results', [])
        if tool_results:
            print(f"   Tool results:")
            for i, result in enumerate(tool_results):
                tool_name = result.get('tool', 'unknown')
                result_data = result.get('result', {})
                print(f"      {i+1}. Tool: {tool_name}")
                if isinstance(result_data, dict):
                    print(f"         Keys: {list(result_data.keys())}")
                    if 'communes' in result_data:
                        communes_count = len(result_data.get('communes', []))
                        print(f"         Communes count: {communes_count}")
        
        # Write detailed results
        with open("test_las_condes_results.txt", "w", encoding="utf-8") as f:
            f.write("TEST LAS CONDES RESULTS\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"1. Direct SearchFarmaciasTool:\n")
            f.write(f"   Total: {result.get('total', 0)}\n")
            f.write(f"   Success: {result.get('success', 'N/A')}\n\n")
            
            f.write(f"2. GetCommunesTool (Región Metropolitana):\n")
            f.write(f"   Total communes: {len(commune_result.get('communes', []))}\n")
            f.write(f"   Las Condes found: {las_condes_found}\n\n")
            
            f.write(f"3. Agent response:\n")
            f.write(f"   Tools used: {response.get('tools_used', [])}\n")
            f.write(f"   Success: {response.get('success', False)}\n")
            f.write(f"   Agent chose get_communes: {'get_communes' in response.get('tools_used', [])}\n")
            f.write(f"   Should have used search_farmacias: True\n\n")
            
            f.write("PROBLEM ANALYSIS:\n")
            if 'get_communes' in response.get('tools_used', []):
                f.write("❌ Agent is using get_communes instead of search_farmacias\n")
                f.write("❌ This suggests the agent thinks it needs to validate the commune first\n")
                f.write("❌ The system prompt may be unclear about when to use each tool\n")
            else:
                f.write("✅ Agent used the correct tool\n")
        
        print("💾 Detailed results saved to: test_las_condes_results.txt")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_las_condes())
