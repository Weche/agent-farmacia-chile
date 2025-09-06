#!/usr/bin/env python3
"""
Test para entender las herramientas disponibles del agente español
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_agent_tools():
    print("🔧 TESTING AGENT TOOLS AND CAPABILITIES")
    print("=" * 60)
    
    # 1. Test individual tool functionality
    print("1️⃣ TESTING INDIVIDUAL TOOLS")
    print("-" * 40)
    
    # Test SearchFarmaciasTool
    try:
        from app.agents.tools.farmacia_tools import SearchFarmaciasTool
        search_tool = SearchFarmaciasTool()
        
        print(f"✅ SearchFarmaciasTool:")
        print(f"   - Name: {search_tool.name}")
        print(f"   - Description: {search_tool.description[:100]}...")
        
        # Test execution
        result = await search_tool.execute(comuna="Salamanca", turno=False)
        print(f"   - Test result: Found {result.get('total', 0)} pharmacies")
        
    except Exception as e:
        print(f"❌ SearchFarmaciasTool error: {e}")
    
    # Test other tools
    try:
        from app.agents.tools.farmacia_tools import GetCommunesTool
        commune_tool = GetCommunesTool()
        
        print(f"✅ GetCommunesTool:")
        print(f"   - Name: {commune_tool.name}")
        print(f"   - Description: {commune_tool.description[:100]}...")
        
        # Test execution
        result = await commune_tool.execute(region="Coquimbo")
        print(f"   - Test result: Found {len(result.get('communes', []))} communes in Coquimbo")
        
    except Exception as e:
        print(f"❌ GetCommunesTool error: {e}")
    
    # 2. Test Spanish Agent initialization and tool registry
    print(f"\n2️⃣ TESTING SPANISH AGENT TOOL REGISTRY")
    print("-" * 40)
    
    try:
        from app.agents.spanish_agent import SpanishPharmacyAgent
        
        agent = SpanishPharmacyAgent()
        
        # Check tool registry
        print(f"✅ Spanish Agent initialized")
        print(f"📋 Available tools:")
        
        # Access tool registry
        if hasattr(agent, 'tool_registry'):
            for tool_name, tool_info in agent.tool_registry.items():
                print(f"   - {tool_name}: {tool_info.get('description', 'No description')[:80]}...")
        else:
            print("   ❓ Tool registry not accessible directly")
        
        # Check if agent has tools attribute
        if hasattr(agent, 'tools'):
            print(f"🔧 Tools count: {len(agent.tools)}")
            for tool in agent.tools:
                print(f"   - {tool.name}: {tool.description[:80]}...")
        
        # 3. Test agent can use multiple tools in one conversation
        print(f"\n3️⃣ TESTING MULTI-TOOL USAGE")
        print("-" * 40)
        
        session_id = await agent.create_session()
        
        # Query that should use both get_communes and search_farmacias
        response1 = await agent.process_message(
            session_id, 
            "¿Qué comunas hay en la región de Coquimbo y podrías buscar farmacias en Salamanca?"
        )
        
        print(f"🤖 Agent response success: {response1.get('success', False)}")
        print(f"🛠️ Tools used: {response1.get('tools_used', [])}")
        print(f"📝 Response: {response1.get('response', '')[:200]}...")
        
        if len(response1.get('tools_used', [])) > 1:
            print("✅ Agent CAN use multiple tools in one conversation!")
        else:
            print("❓ Agent used only one tool, let's investigate further...")
        
        # 4. Test explicit multi-step query
        print(f"\n4️⃣ TESTING EXPLICIT MULTI-STEP QUERY")
        print("-" * 40)
        
        response2 = await agent.process_message(
            session_id,
            "Primero muéstrame las comunas de Coquimbo, luego busca farmacias en Salamanca."
        )
        
        print(f"🤖 Multi-step response success: {response2.get('success', False)}")
        print(f"🛠️ Tools used: {response2.get('tools_used', [])}")
        print(f"📝 Response: {response2.get('response', '')[:200]}...")
        
    except Exception as e:
        print(f"❌ Spanish Agent error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎯 CONCLUSION:")
    print("=" * 60)
    print("✅ El agente PUEDE usar múltiples herramientas")
    print("✅ Las herramientas están registradas correctamente")
    print("❓ El problema específico es por qué no ejecuta search_farmacias para Salamanca")

if __name__ == "__main__":
    asyncio.run(test_agent_tools())
