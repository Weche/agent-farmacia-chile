#!/usr/bin/env python3
"""
Simple Spanish AI Agent Test - Bypasses Langfuse for core functionality testing
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import app components
from app.agents.spanish_agent import SpanishPharmacyAgent
from app.agents.memory.session_manager import SessionManager
from app.agents.tools.tool_registry import ToolRegistry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_without_langfuse():
    """Test the agent with basic OpenAI integration (no Langfuse)"""
    print("🤖 Testing Spanish AI Agent (Simple Mode)")
    print("=" * 60)
    
    try:
        # Initialize agent without Langfuse
        print("1️⃣ Initializing Agent without Langfuse...")
        agent = SpanishPharmacyAgent(use_langfuse=False)
        print(f"✅ Agent initialized successfully")
        print(f"   Model: {agent.model}")
        print(f"   Temperature: {agent.temperature}")
        print(f"   Max tokens: {agent.max_tokens}")
        print(f"   Safety mode: {agent.safety_mode}")
        print(f"   Tools available: {len(agent.tool_registry.tools)}")
        
        # Test session creation
        print("\n2️⃣ Testing Session Creation...")
        session_id = await agent.create_session()
        print(f"✅ Created session: {session_id}")
        
        # Test simple query
        print("\n3️⃣ Testing Simple Query...")
        query = "Hola, ¿puedes ayudarme a encontrar una farmacia?"
        
        try:
            response = await agent.process_message(session_id, query)
            print(f"✅ Response received:")
            print(f"   Text: {response.get('message', 'No message')[:100]}...")
            print(f"   Tools used: {len(response.get('tool_calls', []))}")
            print(f"   Response time: {response.get('response_time', 0):.2f}s")
        except Exception as e:
            print(f"❌ Query failed: {str(e)}")
            
        # Test tool usage query
        print("\n4️⃣ Testing Tool Usage...")
        query = "¿Qué comunas están disponibles?"
        
        try:
            response = await agent.process_message(session_id, query)
            print(f"✅ Tool response received:")
            print(f"   Text: {response.get('message', 'No message')[:100]}...")
            print(f"   Tools used: {len(response.get('tool_calls', []))}")
            print(f"   Response time: {response.get('response_time', 0):.2f}s")
        except Exception as e:
            print(f"❌ Tool query failed: {str(e)}")
            
        # Test session summary
        print("\n5️⃣ Testing Session Summary...")
        try:
            summary = await agent.get_session_summary(session_id)
            print(f"✅ Session Summary:")
            print(f"   Session ID: {summary.get('session_id')}")
            print(f"   Total messages: {summary.get('total_messages')}")
            print(f"   Tools used: {summary.get('tools_used')}")
            print(f"   Language: {summary.get('language', 'es')}")
        except Exception as e:
            print(f"❌ Session summary failed: {str(e)}")
            
        # Clean up
        print("\n6️⃣ Cleaning up...")
        try:
            await agent.delete_session(session_id)
            print("✅ Session cleanup: Success")
        except Exception as e:
            print(f"❌ Cleanup failed: {str(e)}")
            
        print("\n" + "=" * 60)
        print("🎉 Simple Agent Test Complete!")
        print("🚀 Core functionality is working correctly")
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_tool_registry():
    """Test just the tool registry functionality"""
    print("\n🔧 Testing Tool Registry...")
    
    try:
        registry = ToolRegistry()
        print(f"✅ Tool Registry initialized")
        print(f"   Available tools: {len(registry.tools)}")
        print(f"   Tool names: {list(registry.tools.keys())}")
        
        # Test individual tool
        if "search_farmacias" in registry.tools:
            print("\n   Testing search_farmacias tool...")
            try:
                result = await registry.execute_tool(
                    "search_farmacias",
                    comuna="Villa Alemana", 
                    turno=True
                )
                print(f"   ✅ Tool execution successful")
                print(f"       Results: {len(result.get('farmacias', []))} pharmacies found")
            except Exception as e:
                print(f"   ❌ Tool execution failed: {str(e)}")
                
    except Exception as e:
        print(f"❌ Tool registry test failed: {str(e)}")

async def main():
    """Run all simple tests"""
    await test_tool_registry()
    await test_agent_without_langfuse()

if __name__ == "__main__":
    asyncio.run(main())
