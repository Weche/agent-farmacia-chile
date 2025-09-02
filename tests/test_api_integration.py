#!/usr/bin/env python3
"""
Test the updated FastAPI with Spanish AI Agent integration
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_chat_endpoints():
    """Test the new AI agent chat endpoints"""
    print("🤖 Testing Spanish AI Agent API Integration")
    print("=" * 60)
    
    # Test 1: Create new session
    print("1️⃣ Testing session creation...")
    try:
        response = requests.post(f"{BASE_URL}/api/chat/session")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data.get("session_id")
            print(f"   ✅ Session created: {session_id}")
        else:
            print(f"   ❌ Session creation failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 2: Chat with session (session-based endpoint)
    print("\n2️⃣ Testing session-based chat...")
    try:
        chat_payload = {
            "message": "Hola, necesito una farmacia de turno en Santiago",
            "session_id": session_id
        }
        response = requests.post(f"{BASE_URL}/api/chat/message", json=chat_payload)
        if response.status_code == 200:
            chat_response = response.json()
            print(f"   ✅ Response received:")
            print(f"       Reply: {chat_response.get('response', 'No response')[:100]}...")
            print(f"       Tools used: {len(chat_response.get('tools_used', []))}")
            print(f"       Response time: {chat_response.get('response_time_ms', 0):.2f}ms")
        else:
            print(f"   ❌ Chat failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Simple chat endpoint (creates session automatically)
    print("\n3️⃣ Testing simple chat endpoint...")
    try:
        chat_payload = {
            "message": "¿Qué puedes decirme sobre el ibuprofeno?"
        }
        response = requests.post(f"{BASE_URL}/chat", json=chat_payload)
        if response.status_code == 200:
            chat_response = response.json()
            print(f"   ✅ Response received:")
            print(f"       Session ID: {chat_response.get('session_id')}")
            print(f"       Reply: {chat_response.get('reply', 'No reply')[:100]}...")
            print(f"       Tools used: {len(chat_response.get('tools_used', []))}")
            print(f"       Response time: {chat_response.get('response_time_ms', 0):.2f}ms")
        else:
            print(f"   ❌ Chat failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Get session history
    print("\n4️⃣ Testing session history...")
    try:
        response = requests.get(f"{BASE_URL}/api/chat/history/{session_id}")
        if response.status_code == 200:
            history = response.json()
            print(f"   ✅ History retrieved:")
            print(f"       Session ID: {history.get('session_id')}")
            print(f"       Total messages: {history.get('total_messages')}")
            print(f"       Language: {history.get('language')}")
            print(f"       Agent model: {history.get('agent_model')}")
        else:
            print(f"   ❌ History retrieval failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Delete session
    print("\n5️⃣ Testing session deletion...")
    try:
        response = requests.delete(f"{BASE_URL}/api/chat/session/{session_id}")
        if response.status_code == 200:
            delete_response = response.json()
            print(f"   ✅ Session deleted: {delete_response.get('status')}")
        else:
            print(f"   ❌ Session deletion failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 API Integration Test Complete!")
    print("🚀 Spanish AI Agent is now available via REST API!")

def test_legacy_endpoints():
    """Test that existing endpoints still work"""
    print("\n🔧 Testing legacy endpoints...")
    
    try:
        # Test pharmacy search
        response = requests.get(f"{BASE_URL}/api/search?comuna=Santiago")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Pharmacy search: {len(data.get('results', []))} pharmacies found")
        
        # Test stats
        response = requests.get(f"{BASE_URL}/api/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Stats endpoint: {stats.get('total')} total pharmacies")
            
        # Test legacy chat
        response = requests.post(f"{BASE_URL}/chat/legacy", json={"message": "farmacia santiago"})
        if response.status_code == 200:
            print(f"   ✅ Legacy chat: Still working")
            
    except Exception as e:
        print(f"   ❌ Legacy test error: {e}")

if __name__ == "__main__":
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    test_chat_endpoints()
    test_legacy_endpoints()
