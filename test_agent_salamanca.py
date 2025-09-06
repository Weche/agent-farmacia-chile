#!/usr/bin/env python3
"""
Test específico para diagnosticar el problema del agente con Salamanca
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.spanish_agent import SpanishPharmacyAgent

async def test_agent_salamanca():
    print("🧪 TESTING SPANISH AGENT SALAMANCA ISSUE")
    print("=" * 60)
    
    # Initialize agent
    agent = SpanishPharmacyAgent()
    
    # Create session
    session_id = await agent.create_session()
    print(f"📝 Session created: {session_id}")
    
    # Test the exact query that's failing
    query = "hay farmacias en salamanca?"
    print(f"\n🔍 Testing query: '{query}'")
    
    # Process message
    response = await agent.process_message(session_id, query)
    
    print("\n📋 RESPONSE ANALYSIS:")
    print(f"Success: {response.get('success', False)}")
    print(f"Response: {response.get('response', '')[:200]}...")
    print(f"Tools used: {response.get('tools_used', [])}")
    print(f"Tool results: {len(response.get('tool_results', []))} results")
    
    # Check if SearchFarmaciasTool was used
    search_tool_used = 'SearchFarmaciasTool' in response.get('tools_used', [])
    print(f"\n🔧 SearchFarmaciasTool executed: {search_tool_used}")
    
    if not search_tool_used:
        print("❌ PROBLEM: SearchFarmaciasTool was NOT executed")
        print("🔍 Checking tools...")
        # Check what tools the agent has
        if hasattr(agent, 'mcp_client') and hasattr(agent.mcp_client, 'tools'):
            tools = agent.mcp_client.tools
            print(f"Available tools: {list(tools.keys())}")
        else:
            print("Could not access agent tools directly")
    
    # Check tool results
    tool_results = response.get('tool_results', [])
    if tool_results:
        print(f"\n📊 TOOL RESULTS ({len(tool_results)} total):")
        for i, result in enumerate(tool_results):
            print(f"   {i+1}. Tool: {result.get('tool_name', 'Unknown')}")
            print(f"      Success: {result.get('success', False)}")
            if 'result' in result:
                result_str = str(result['result'])[:100]
                print(f"      Result: {result_str}...")
    
    # Test with more direct query
    print(f"\n🎯 Testing more direct query...")
    direct_query = "buscar farmacias en salamanca"
    response2 = await agent.process_message(session_id, direct_query)
    
    search_tool_used2 = 'SearchFarmaciasTool' in response2.get('tools_used', [])
    print(f"Direct query tools used: {response2.get('tools_used', [])}")
    print(f"SearchFarmaciasTool executed: {search_tool_used2}")
    
    # Clean up
    await agent.delete_session(session_id)

if __name__ == "__main__":
    asyncio.run(test_agent_salamanca())
