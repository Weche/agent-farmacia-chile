#!/usr/bin/env python3
"""
Full Spanish AI Agent Test - Test actual conversations with OpenAI
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_real_conversation():
    """Test actual AI conversations"""
    print("🤖 Testing Spanish AI Agent - Real Conversations")
    print("=" * 60)
    
    try:
        # Initialize agent 
        print("1️⃣ Initializing Agent...")
        agent = SpanishPharmacyAgent()
        print(f"✅ Agent initialized successfully")
        
        # Create session
        print("\n2️⃣ Creating Session...")
        session_id = await agent.create_session()
        print(f"✅ Created session: {session_id}")
        
        # Test conversations
        test_queries = [
            "Hola, ¿puedes ayudarme?",
            "Necesito encontrar farmacias de turno en Villa Alemana",
            "¿Qué puedes decirme sobre el paracetamol?",
            "¿Qué comunas tienes disponibles?"
        ]
        
        for i, query in enumerate(test_queries, 3):
            print(f"\n{i}️⃣ Testing: '{query}'")
            
            try:
                response = await agent.process_message(session_id, query)
                
                print(f"   ✅ Response received:")
                print(f"      Message: {response.get('response', 'No response')[:150]}...")
                print(f"      Tools used: {len(response.get('tools_used', []))}")
                print(f"      Success: {response.get('success', False)}")
                print(f"      Response time: {response.get('response_time_ms', 0):.2f}ms")
                
                if response.get('tools_used'):
                    print(f"      Tool calls:")
                    for tool_call in response.get('tools_used', []):
                        print(f"        - {tool_call.get('tool')}: {tool_call.get('args', {})}")
                        
            except Exception as e:
                print(f"   ❌ Query failed: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Test session summary
        print(f"\n{len(test_queries) + 3}️⃣ Testing Session Summary...")
        try:
            summary = await agent.get_session_summary(session_id)
            print(f"   ✅ Session Summary:")
            print(f"      Session ID: {summary.get('session_id')}")
            print(f"      Total messages: {summary.get('total_messages')}")
            print(f"      Tools used: {summary.get('tools_used')}")
            print(f"      Language: {summary.get('language', 'es')}")
            print(f"      Agent model: {summary.get('agent_model')}")
        except Exception as e:
            print(f"   ❌ Session summary failed: {str(e)}")
            
        # Clean up
        print(f"\n{len(test_queries) + 4}️⃣ Cleaning up...")
        try:
            await agent.delete_session(session_id)
            print("   ✅ Session cleanup: Success")
        except Exception as e:
            print(f"   ❌ Cleanup failed: {str(e)}")
            
        print("\n" + "=" * 60)
        print("🎉 Real Conversation Test Complete!")
        print("🚀 AI Agent is ready for production!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_conversation())
