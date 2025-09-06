#!/usr/bin/env python3
"""
Test específico para el problema de Salamanca con debugging detallado
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class DebugOutput:
    def __init__(self, filename):
        self.filename = filename
        self.lines = []
        
    def print(self, *args, **kwargs):
        """Print to both console and file buffer"""
        message = " ".join(str(arg) for arg in args)
        print(message, **kwargs)
        self.lines.append(message)
        
    def save(self):
        """Save all output to file"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write(f"SALAMANCA AGENT DEBUG REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            for line in self.lines:
                f.write(line + "\n")

async def test_salamanca_debug():
async def test_salamanca_debug():
    # Initialize debug output
    debug_out = DebugOutput("salamanca_debug_results.txt")
    
    debug_out.print("🔍 DEBUGGING SALAMANCA AGENT ISSUE")
    debug_out.print("=" * 60)
    
    try:
        from app.agents.spanish_agent import SpanishPharmacyAgent
        
        # 1. Initialize agent and check tools
        debug_out.print("1️⃣ INITIALIZING AGENT AND CHECKING TOOLS")
        debug_out.print("-" * 40)
        
        agent = SpanishPharmacyAgent()
        
        # Check available tools
        if hasattr(agent, 'tool_registry') and hasattr(agent.tool_registry, 'tools'):
            available_tools = list(agent.tool_registry.tools.keys())
            debug_out.print(f"✅ Available tools: {available_tools}")
            
            # Check if search_farmacias is available
            if 'search_farmacias' in available_tools:
                debug_out.print("✅ search_farmacias tool is registered")
                search_tool = agent.tool_registry.tools['search_farmacias']
                debug_out.print(f"   - Tool class: {type(search_tool).__name__}")
                debug_out.print(f"   - Tool description: {search_tool.description[:100]}...")
            else:
                debug_out.print("❌ search_farmacias tool NOT found in registry!")
                
            if 'get_communes' in available_tools:
                debug_out.print("✅ get_communes tool is registered")
                commune_tool = agent.tool_registry.tools['get_communes']
                debug_out.print(f"   - Tool class: {type(commune_tool).__name__}")
                debug_out.print(f"   - Tool description: {commune_tool.description[:100]}...")
        else:
            debug_out.print("❌ Cannot access tool registry")
        
        # 2. Test specific Salamanca queries
        debug_out.print(f"\n2️⃣ TESTING SALAMANCA QUERIES")
        debug_out.print("-" * 40)
        
        session_id = await agent.create_session()
        
        # Test different phrasings that should trigger search_farmacias
        test_queries = [
            "Busca farmacias en Salamanca",
            "¿Hay farmacias en la comuna de Salamanca?",
            "Necesito encontrar farmacias en Salamanca"
        ]
        
        for i, query in enumerate(test_queries, 1):
            debug_out.print(f"\n🧪 Test {i}: '{query}'")
            response = await agent.process_message(session_id, query)
            
            tools_used = response.get('tools_used', [])
            success = response.get('success', False)
            
            debug_out.print(f"   ✅ Success: {success}")
            debug_out.print(f"   🛠️ Tools used: {tools_used}")
            
            # Check if search_farmacias was used
            if 'search_farmacias' in tools_used:
                debug_out.print("   ✅ search_farmacias was executed!")
                
                # Check for results
                tool_results = response.get('tool_results', [])
                if tool_results:
                    for result in tool_results:
                        if result.get('tool') == 'search_farmacias':
                            total = result.get('result', {}).get('total', 0)
                            debug_out.print(f"   📊 Found {total} pharmacies")
                else:
                    debug_out.print("   ⚠️ No tool results found")
            else:
                debug_out.print("   ❌ search_farmacias was NOT executed")
                
            # Show partial response
            agent_reply = response.get('response', '')
            debug_out.print(f"   💬 Response preview: {agent_reply[:150]}...")
            
            # Show tool results details
            tool_results = response.get('tool_results', [])
            if tool_results:
                debug_out.print(f"   📋 Tool results count: {len(tool_results)}")
                for j, result in enumerate(tool_results):
                    tool_name = result.get('tool', 'unknown')
                    result_data = result.get('result', {})
                    debug_out.print(f"      {j+1}. Tool: {tool_name}")
                    if isinstance(result_data, dict):
                        for key, value in list(result_data.items())[:3]:  # Show first 3 keys
                            debug_out.print(f"         {key}: {str(value)[:50]}...")
            
            debug_out.print("-" * 30)
    
        # 3. Test system prompt inspection
        debug_out.print(f"\n3️⃣ SYSTEM PROMPT ANALYSIS")
        debug_out.print("-" * 40)
        
        system_prompt = agent.system_prompt
        
        # Check if search_farmacias is mentioned in system prompt
        if 'search_farmacias' in system_prompt:
            debug_out.print("✅ search_farmacias is mentioned in system prompt")
        else:
            debug_out.print("❌ search_farmacias is NOT mentioned in system prompt")
            
        # Check specific instructions
        key_phrases = [
            "buscar farmacias por comuna",
            "search_farmacias",
            "herramientas disponibles",
            "busca farmacias"
        ]
        
        for phrase in key_phrases:
            if phrase.lower() in system_prompt.lower():
                debug_out.print(f"✅ Found: '{phrase}'")
            else:
                debug_out.print(f"❌ Missing: '{phrase}'")
        
        # Show relevant section of system prompt
        debug_out.print(f"\n📋 System prompt length: {len(system_prompt)} characters")
        if 'HERRAMIENTAS DISPONIBLES' in system_prompt:
            start = system_prompt.find('HERRAMIENTAS DISPONIBLES')
            end = start + 500
            tools_section = system_prompt[start:end]
            debug_out.print(f"📋 Tools section preview:\n{tools_section}...")
        
        # 4. Test direct tool comparison
        debug_out.print(f"\n4️⃣ DIRECT TOOL COMPARISON")
        debug_out.print("-" * 40)
        
        # Test search_farmacias directly
        if 'search_farmacias' in available_tools:
            search_tool = agent.tool_registry.tools['search_farmacias']
            direct_result = await search_tool.execute(comuna="Salamanca", turno=False)
            debug_out.print(f"🔧 Direct search_farmacias test:")
            debug_out.print(f"   Success: {direct_result.get('success', 'N/A')}")
            debug_out.print(f"   Total: {direct_result.get('total', 0)}")
            if direct_result.get('farmacias'):
                debug_out.print(f"   First pharmacy: {direct_result['farmacias'][0].get('nombre', 'N/A')}")
        
        # Test get_communes directly  
        if 'get_communes' in available_tools:
            commune_tool = agent.tool_registry.tools['get_communes']
            commune_result = await commune_tool.execute(region="Coquimbo")
            debug_out.print(f"🔧 Direct get_communes test:")
            debug_out.print(f"   Success: {commune_result.get('success', 'N/A')}")
            debug_out.print(f"   Communes count: {len(commune_result.get('communes', []))}")
            if commune_result.get('communes'):
                debug_out.print(f"   Sample communes: {commune_result['communes'][:5]}")
    
    except Exception as e:
        debug_out.print(f"❌ ERROR: {e}")
        import traceback
        debug_out.print(traceback.format_exc())
    
    finally:
        # Save results to file
        debug_out.save()
        debug_out.print(f"\n💾 Results saved to: salamanca_debug_results.txt")

if __name__ == "__main__":
    asyncio.run(test_salamanca_debug())
