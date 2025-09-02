#!/usr/bin/env python3
"""
Test Las Condes agent responses specifically
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.spanish_agent import SpanishPharmacyAgent
from app.agents.memory.conversation_memory import ConversationMemory
from app.agents.memory.session_manager import SessionManager

async def test_villa_alemana_search():
    """Test Las Condes pharmacy search"""
    print("🧪 Testing Las Condes agent search...")
    
    # Initialize components
    agent = SpanishPharmacyAgent()
    session_manager = SessionManager()
    
    # Create a test session
    session_id = "test_villa_alemana"
    session_info = session_manager.create_session(session_id)
    memory = ConversationMemory(session_id=session_id)
    
    # Test message
    test_message = "Necesito farmacias en Las Condes que estén de turno"
    
    print(f"📝 Sending message: {test_message}")
    
    try:
        response = await agent.process_message(test_message, memory)
        
        print(f"✅ Response received:")
        print(f"Content: {response.get('content', 'No content')}")
        print(f"Has tools: {bool(response.get('tool_calls'))}")
        
        if response.get('tool_calls'):
            print(f"Tool calls: {len(response['tool_calls'])}")
            for i, tool_call in enumerate(response['tool_calls']):
                print(f"  Tool {i+1}: {tool_call.get('name', 'Unknown')}")
                print(f"    Args: {tool_call.get('arguments', {})}")
        
        # Also test direct tool execution
        print("\n🔧 Testing direct tool execution...")
        from app.agents.tools.tool_registry import get_tool_registry
        
        registry = get_tool_registry()
        tool_result = await registry.execute_tool("search_farmacias", comuna="Las Condes", turno=True)
        
        print(f"Direct tool result: {tool_result}")
        
        if tool_result.get('success'):
            farmacias = tool_result.get('data', {}).get('farmacias', [])
            print(f"Found {len(farmacias)} pharmacies directly")
            for farmacia in farmacias[:3]:  # Show first 3
                print(f"  - {farmacia.get('nombre', 'Unknown')}")
        else:
            print(f"❌ Direct tool execution failed: {tool_result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_villa_alemana_search())
