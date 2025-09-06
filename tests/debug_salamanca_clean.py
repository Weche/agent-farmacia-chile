#!/usr/bin/env python3
"""
Test específico para el problema de Salamanca con debugging detallado
Output a archivo de texto para análisis
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Configure detailed logging
logging.basicConfig(level=logging.INFO)
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
    """Test del agente con output a archivo"""
    debug_out = DebugOutput("salamanca_debug_results.txt")
    
    debug_out.print("🔍 DEBUGGING SALAMANCA AGENT ISSUE")
    debug_out.print("=" * 60)
    
    try:
        from app.agents.spanish_agent import SpanishPharmacyAgent
        
        # 1. Initialize agent
        debug_out.print("1️⃣ INITIALIZING AGENT")
        debug_out.print("-" * 40)
        
        agent = SpanishPharmacyAgent()
        debug_out.print("✅ Agent initialized successfully")
        
        # 2. Check tools
        if hasattr(agent, 'tool_registry') and hasattr(agent.tool_registry, 'tools'):
            available_tools = list(agent.tool_registry.tools.keys())
            debug_out.print(f"✅ Available tools: {available_tools}")
            
            if 'search_farmacias' in available_tools:
                debug_out.print("✅ search_farmacias tool is registered")
            else:
                debug_out.print("❌ search_farmacias tool NOT found!")
                
            if 'get_communes' in available_tools:
                debug_out.print("✅ get_communes tool is registered")
        else:
            debug_out.print("❌ Cannot access tool registry")
        
        # 3. Test Salamanca queries
        debug_out.print(f"\n2️⃣ TESTING SALAMANCA QUERIES")
        debug_out.print("-" * 40)
        
        session_id = await agent.create_session()
        
        test_queries = [
            "Busca farmacias en Salamanca",
            "¿Hay farmacias en la comuna de Salamanca?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            debug_out.print(f"\n🧪 Test {i}: '{query}'")
            response = await agent.process_message(session_id, query)
            
            tools_used = response.get('tools_used', [])
            success = response.get('success', False)
            
            debug_out.print(f"   ✅ Success: {success}")
            debug_out.print(f"   🛠️ Tools used: {tools_used}")
            
            if 'search_farmacias' in tools_used:
                debug_out.print("   ✅ search_farmacias was executed!")
            else:
                debug_out.print("   ❌ search_farmacias was NOT executed")
                
            agent_reply = response.get('response', '')
            debug_out.print(f"   💬 Response: {agent_reply[:200]}...")
        
        # 4. System prompt check
        debug_out.print(f"\n3️⃣ SYSTEM PROMPT CHECK")
        debug_out.print("-" * 40)
        
        system_prompt = agent.system_prompt
        debug_out.print(f"📋 System prompt length: {len(system_prompt)} characters")
        
        if 'search_farmacias' in system_prompt:
            debug_out.print("✅ search_farmacias mentioned in prompt")
        else:
            debug_out.print("❌ search_farmacias NOT mentioned in prompt")
        
        # 5. Direct tool test
        debug_out.print(f"\n4️⃣ DIRECT TOOL TEST")
        debug_out.print("-" * 40)
        
        if 'search_farmacias' in available_tools:
            search_tool = agent.tool_registry.tools['search_farmacias']
            direct_result = await search_tool.execute(comuna="Salamanca", turno=False)
            debug_out.print(f"🔧 Direct search_farmacias result:")
            debug_out.print(f"   Total: {direct_result.get('total', 0)}")
            debug_out.print(f"   Success: {direct_result.get('success', 'N/A')}")
    
    except Exception as e:
        debug_out.print(f"❌ ERROR: {e}")
        import traceback
        debug_out.print(traceback.format_exc())
    
    finally:
        debug_out.save()
        debug_out.print(f"\n💾 Results saved to: salamanca_debug_results.txt")

if __name__ == "__main__":
    asyncio.run(test_salamanca_debug())
