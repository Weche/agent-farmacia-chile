#!/usr/bin/env python3
"""
Standalone AI Agent Test Suite
Comprehensive testing without interfering with the running server
"""
import sys
import os
import time
import requests
import json
from datetime import datetime

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_step(step_num, description):
    """Print a test step"""
    print(f"\n📋 Step {step_num}: {description}")
    print("-" * 50)

def test_server_health():
    """Test basic server health"""
    print_step(1, "Server Health Check")
    
    try:
        start_time = time.time()
        response = requests.get('http://127.0.0.1:8001/api/stats', timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server Status: OK ({response_time:.0f}ms)")
            print(f"📊 Pharmacy Data: {data.get('total', 'N/A')} total, {data.get('turno', 'N/A')} on duty")
            return True
        else:
            print(f"❌ Server Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Server Health Check Failed: {e}")
        return False

def test_chat_session_creation():
    """Test creating a new chat session"""
    print_step(2, "Chat Session Creation")
    
    try:
        response = requests.post('http://127.0.0.1:8001/api/chat/session', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"✅ Session Created: {session_id[:12]}...")
            print(f"📅 Created At: {data.get('created_at')}")
            return session_id
        else:
            print(f"❌ Session Creation Failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Session Creation Error: {e}")
        return None

def test_ai_conversation(session_id):
    """Test AI conversation with multiple messages"""
    if not session_id:
        print("❌ Cannot test conversation without valid session")
        return False
    
    print_step(3, "AI Conversation Test")
    
    # Test messages with different complexity levels
    test_messages = [
        {
            "message": "Hola, necesito ayuda para encontrar una farmacia",
            "expected_tools": ["get_communes"],
            "description": "Simple greeting"
        },
        {
            "message": "Busco farmacias en Santiago que tengan ibuprofeno",
            "expected_tools": ["search_farmacias", "lookup_medicamento"],
            "description": "Pharmacy search with medication"
        },
        {
            "message": "¿Qué comunas están disponibles?",
            "expected_tools": ["get_communes"],
            "description": "Available communes query"
        }
    ]
    
    conversation_success = True
    
    for i, test_case in enumerate(test_messages, 1):
        print(f"\n🗨️  Message {i}: {test_case['description']}")
        print(f"📝 Query: '{test_case['message']}'")
        
        try:
            start_time = time.time()
            response = requests.post(
                f'http://127.0.0.1:8001/api/chat/message?session_id={session_id}',
                json={"message": test_case["message"]},
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                tools_used = data.get('tools_used', [])
                
                print(f"✅ Response Time: {response_time:.0f}ms")
                print(f"🤖 AI Response: {ai_response[:100]}{'...' if len(ai_response) > 100 else ''}")
                
                if tools_used:
                    print(f"🔧 Tools Used: {', '.join(tools_used)}")
                    
                    # Check if expected tools were used
                    expected_found = any(tool in tools_used for tool in test_case['expected_tools'])
                    if expected_found:
                        print(f"✅ Expected tool usage confirmed")
                    else:
                        print(f"⚠️  Expected tools {test_case['expected_tools']} not found in {tools_used}")
                else:
                    print("📝 No tools used (conversation only)")
                
            else:
                print(f"❌ Message {i} Failed: {response.status_code}")
                conversation_success = False
                
        except Exception as e:
            print(f"❌ Message {i} Error: {e}")
            conversation_success = False
            
        # Small delay between messages
        time.sleep(1)
    
    return conversation_success

def test_conversation_history(session_id):
    """Test conversation history retrieval"""
    if not session_id:
        print("❌ Cannot test history without valid session")
        return False
        
    print_step(4, "Conversation History Test")
    
    try:
        response = requests.get(f'http://127.0.0.1:8001/api/chat/history/{session_id}', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            conversation = data.get('conversation', [])
            
            print(f"✅ History Retrieved: {len(conversation)} messages")
            
            # Show last few messages
            if conversation:
                print(f"📜 Last message: {conversation[-1].get('content', '')[:80]}...")
                
                # Count user vs assistant messages
                user_msgs = sum(1 for msg in conversation if msg.get('role') == 'user')
                assistant_msgs = sum(1 for msg in conversation if msg.get('role') == 'assistant')
                
                print(f"👤 User messages: {user_msgs}")
                print(f"🤖 Assistant messages: {assistant_msgs}")
                
            return True
        else:
            print(f"❌ History Retrieval Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ History Retrieval Error: {e}")
        return False

def test_session_cleanup(session_id):
    """Test session deletion"""
    if not session_id:
        print("❌ Cannot test cleanup without valid session")
        return False
        
    print_step(5, "Session Cleanup Test")
    
    try:
        response = requests.delete(f'http://127.0.0.1:8001/api/chat/session/{session_id}', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Session Deleted: {data.get('message', 'Success')}")
            return True
        else:
            print(f"❌ Session Deletion Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Session Deletion Error: {e}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print_step(6, "Error Handling Test")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Invalid session ID
    try:
        response = requests.post(
            'http://127.0.0.1:8001/api/chat/message?session_id=invalid-session-id',
            json={"message": "test"},
            timeout=10
        )
        if response.status_code in [400, 404]:
            print("✅ Invalid session handling: OK")
            tests_passed += 1
        else:
            print(f"⚠️  Invalid session handling: Unexpected status {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid session test error: {e}")
    
    # Test 2: Empty message
    try:
        session_response = requests.post('http://127.0.0.1:8001/api/chat/session', timeout=10)
        if session_response.status_code == 200:
            temp_session = session_response.json()['session_id']
            
            response = requests.post(
                f'http://127.0.0.1:8001/api/chat/message?session_id={temp_session}',
                json={"message": ""},
                timeout=10
            )
            if response.status_code in [200, 400]:
                print("✅ Empty message handling: OK")
                tests_passed += 1
            else:
                print(f"⚠️  Empty message handling: Unexpected status {response.status_code}")
                
            # Cleanup temp session
            requests.delete(f'http://127.0.0.1:8001/api/chat/session/{temp_session}')
    except Exception as e:
        print(f"❌ Empty message test error: {e}")
    
    # Test 3: Very long message
    try:
        session_response = requests.post('http://127.0.0.1:8001/api/chat/session', timeout=10)
        if session_response.status_code == 200:
            temp_session = session_response.json()['session_id']
            
            long_message = "Necesito farmacia " * 200  # Very long message
            response = requests.post(
                f'http://127.0.0.1:8001/api/chat/message?session_id={temp_session}',
                json={"message": long_message},
                timeout=30
            )
            if response.status_code == 200:
                print("✅ Long message handling: OK")
                tests_passed += 1
            else:
                print(f"⚠️  Long message handling: Status {response.status_code}")
                
            # Cleanup temp session
            requests.delete(f'http://127.0.0.1:8001/api/chat/session/{temp_session}')
    except Exception as e:
        print(f"❌ Long message test error: {e}")
    
    print(f"📊 Error Handling Tests: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests

def main():
    """Main test execution"""
    print_header("Spanish Pharmacy AI Agent - Standalone Test Suite")
    print(f"🕐 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Target Server: http://127.0.0.1:8001")
    
    # Test execution
    all_tests_passed = True
    session_id = None
    
    try:
        # 1. Server Health
        if not test_server_health():
            print("\n❌ Server health check failed. Aborting tests.")
            return False
        
        # 2. Session Creation
        session_id = test_chat_session_creation()
        if not session_id:
            print("\n❌ Session creation failed. Aborting conversation tests.")
            all_tests_passed = False
        
        # 3. AI Conversation
        if session_id and not test_ai_conversation(session_id):
            print("\n⚠️  AI conversation tests had issues.")
            all_tests_passed = False
        
        # 4. History Retrieval
        if session_id and not test_conversation_history(session_id):
            print("\n⚠️  History retrieval test failed.")
            all_tests_passed = False
        
        # 5. Error Handling
        if not test_error_handling():
            print("\n⚠️  Error handling tests had issues.")
            all_tests_passed = False
        
        # 6. Session Cleanup
        if session_id and not test_session_cleanup(session_id):
            print("\n⚠️  Session cleanup test failed.")
            all_tests_passed = False
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        if session_id:
            print("🧹 Cleaning up session...")
            try:
                requests.delete(f'http://127.0.0.1:8001/api/chat/session/{session_id}', timeout=5)
            except:
                pass
        return False
    
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        all_tests_passed = False
    
    # Final Results
    print_header("Test Results Summary")
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Spanish Pharmacy AI Agent is fully functional")
        print("✅ API endpoints are working correctly")
        print("✅ Session management is operational")
        print("✅ AI conversation flow is smooth")
        print("✅ Error handling is robust")
    else:
        print("⚠️  SOME TESTS FAILED OR HAD ISSUES")
        print("Please review the output above for details")
    
    print(f"\n🕐 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
