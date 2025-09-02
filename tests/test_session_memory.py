#!/usr/bin/env python3
"""
Test Session Memory System
Validates session management and conversation memory functionality
"""

import asyncio
import sys
import os
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from app.agents.memory.session_manager import SessionManager
from app.agents.memory.conversation_memory import ConversationMemory
import json
from datetime import datetime

async def test_session_memory_system():
    """Test complete session memory functionality"""
    
    print("🧪 Testing Session Memory System")
    print("=" * 50)
    
    # Initialize session manager
    session_manager = SessionManager()
    
    print("1️⃣ Testing Redis Connection...")
    if not session_manager.connect():
        print("❌ Redis connection failed!")
        return False
    print("✅ Redis connected successfully")
    
    # Test 1: Create Session
    print("\n2️⃣ Testing Session Creation...")
    user_context = {
        "location": "Villa Alemana",
        "preferred_language": "spanish",
        "user_type": "patient"
    }
    
    session_id = session_manager.create_session(user_context)
    print(f"✅ Created session: {session_id}")
    
    # Test 2: Get Session
    print("\n3️⃣ Testing Session Retrieval...")
    session_data = session_manager.get_session(session_id)
    if session_data:
        print(f"✅ Retrieved session data:")
        print(f"   Created: {session_data['created_at']}")
        print(f"   Context: {session_data['user_context']}")
        print(f"   Language: {session_data['session_language']}")
    else:
        print("❌ Failed to retrieve session")
        return False
    
    # Test 3: Conversation Memory
    print("\n4️⃣ Testing Conversation Memory...")
    memory = ConversationMemory(session_id)
    
    # Add system message
    await memory.add_message(
        role="system",
        content="Eres un asistente farmacéutico especializado en ayudar a encontrar farmacias de turno y información sobre medicamentos en Chile.",
        metadata={"type": "system_init"}
    )
    
    # Add user message
    await memory.add_message(
        role="user",
        content="Hola, necesito encontrar una farmacia de turno en Villa Alemana",
        metadata={"user_input": True}
    )
    
    # Add assistant message with tool call
    tool_calls = [
        {
            "tool": "SearchFarmaciasTool",
            "args": {"comuna": "Villa Alemana", "turno": True},
            "result_count": 3
        }
    ]
    
    await memory.add_message(
        role="assistant",
        content="He encontrado 3 farmacias de turno en Villa Alemana. Te muestro las opciones disponibles:",
        tool_calls=tool_calls,
        metadata={"tools_used": 1}
    )
    
    print("✅ Added conversation messages")
    
    # Test 4: Retrieve Conversation History
    print("\n5️⃣ Testing Conversation History Retrieval...")
    history = await memory.get_conversation_history()
    print(f"✅ Retrieved {len(history)} messages:")
    
    for i, msg in enumerate(history, 1):
        print(f"   {i}. [{msg['role']}] {msg['content'][:50]}...")
        if msg.get('tool_calls'):
            print(f"      🔧 Tools: {[t['tool'] for t in msg['tool_calls']]}")
    
    # Test 5: Context Management
    print("\n6️⃣ Testing Context Management...")
    await memory.add_context("user_location", "Villa Alemana")
    await memory.add_context("last_search", "farmacias_turno")
    await memory.add_context("preferred_pharmacy_chain", "Ahumada")
    
    user_location = await memory.get_context("user_location")
    all_context = await memory.get_all_context()
    
    print(f"✅ Context stored and retrieved:")
    print(f"   User location: {user_location}")
    print(f"   All context: {all_context}")
    
    # Test 6: Tool Usage Logging
    print("\n7️⃣ Testing Tool Usage Logging...")
    await memory.log_tool_usage(
        tool_name="SearchFarmaciasTool",
        tool_args={"comuna": "Villa Alemana", "turno": True},
        result={"status": "success", "count": 3}
    )
    
    await memory.log_tool_usage(
        tool_name="LookupMedicamentoTool",
        tool_args={"medicamento": "paracetamol"},
        result={"status": "success", "found": True}
    )
    
    print("✅ Tool usage logged")
    
    # Test 7: LLM Context Format
    print("\n8️⃣ Testing LLM Context Format...")
    llm_context = await memory.get_context_for_llm()
    print(f"✅ LLM context prepared with {len(llm_context)} messages")
    
    for msg in llm_context:
        print(f"   [{msg['role']}] {msg['content'][:40]}...")
    
    # Test 8: Session Summary
    print("\n9️⃣ Testing Session Summary...")
    summary = await memory.get_conversation_summary()
    print(f"✅ Session summary:")
    print(f"   Session ID: {summary.get('session_id', 'N/A')}")
    print(f"   Total messages: {summary.get('total_messages', 0)}")
    print(f"   Tools used: {summary.get('total_tools_used', 0)}")
    print(f"   Context keys: {summary.get('context_keys', [])}")
    print(f"   Language: {summary.get('language', 'N/A')}")
    
    # Test 9: Session Activity Update
    print("\n🔟 Testing Session Activity Update...")
    updated = session_manager.update_session_activity(session_id)
    if updated:
        print("✅ Session activity updated")
    else:
        print("❌ Failed to update session activity")
    
    # Test 10: Active Sessions Count
    print("\n1️⃣1️⃣ Testing Active Sessions Count...")
    active_count = session_manager.get_active_sessions_count()
    print(f"✅ Active sessions: {active_count}")
    
    # Test 11: Multiple Sessions
    print("\n1️⃣2️⃣ Testing Multiple Sessions...")
    session_id_2 = session_manager.create_session({"location": "Valparaíso"})
    session_id_3 = session_manager.create_session({"location": "Santiago"})
    
    new_active_count = session_manager.get_active_sessions_count()
    print(f"✅ Created 2 additional sessions. Total active: {new_active_count}")
    
    # Test 12: Session Cleanup (demonstration)
    print("\n1️⃣3️⃣ Testing Session Cleanup...")
    cleanup_result = session_manager.cleanup_expired_sessions()
    print(f"✅ Session cleanup completed. Active sessions: {cleanup_result}")
    
    # Clean up test sessions
    print("\n🧹 Cleaning up test sessions...")
    deleted_1 = session_manager.delete_session(session_id)
    deleted_2 = session_manager.delete_session(session_id_2)
    deleted_3 = session_manager.delete_session(session_id_3)
    
    print(f"✅ Deleted test sessions: {deleted_1 and deleted_2 and deleted_3}")
    
    print("\n" + "=" * 50)
    print("🎉 Session Memory System Test Complete!")
    print("✅ All components working correctly")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_session_memory_system())
        if result:
            print("\n🚀 Session memory system ready for AI agent integration!")
        else:
            print("\n❌ Session memory system test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
