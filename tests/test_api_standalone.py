#!/usr/bin/env python3
"""
Standalone API Test Script
Tests the Spanish AI Agent API endpoints without affecting the running server
This script can be run independently while the server is running
"""

import requests
import json
import time
import sys
from typing import Optional

class APITester:
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        
    def test_server_health(self) -> bool:
        """Test if server is responding"""
        try:
            response = requests.get(f"{self.base_url}/api/stats", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def test_legacy_endpoints(self) -> bool:
        """Test existing endpoints to ensure they still work"""
        print("🔧 Testing Legacy Endpoints...")
        
        try:
            # Test stats endpoint
            response = requests.get(f"{self.base_url}/api/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                print(f"   ✅ Stats: {stats.get('total')} total pharmacies, {stats.get('turno')} on duty")
            else:
                print(f"   ❌ Stats failed: {response.status_code}")
                return False
            
            # Test pharmacy search
            response = requests.get(f"{self.base_url}/api/search?comuna=Santiago", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Search: Found {len(data.get('results', []))} pharmacies in Santiago")
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                return False
                
            # Test communes endpoint
            response = requests.get(f"{self.base_url}/api/communes", timeout=10)
            if response.status_code == 200:
                communes = response.json()
                print(f"   ✅ Communes: {len(communes)} available")
            else:
                print(f"   ❌ Communes failed: {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            print(f"   ❌ Legacy test error: {e}")
            return False
    
    def test_ai_session_creation(self) -> bool:
        """Test AI agent session creation"""
        print("\n🤖 Testing AI Agent Session Creation...")
        
        try:
            response = requests.post(f"{self.base_url}/api/chat/session", timeout=15)
            if response.status_code == 200:
                session_data = response.json()
                self.session_id = session_data.get("session_id")
                print(f"   ✅ Session created: {self.session_id}")
                return True
            else:
                print(f"   ❌ Session creation failed: {response.status_code}")
                print(f"       Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Session creation error: {e}")
            return False
    
    def test_ai_simple_chat(self) -> bool:
        """Test simple AI chat without tools"""
        print("\n💬 Testing Simple AI Chat...")
        
        try:
            chat_payload = {
                "message": "Hola, ¿puedes ayudarme?"
            }
            response = requests.post(f"{self.base_url}/chat", json=chat_payload, timeout=20)
            
            if response.status_code == 200:
                chat_response = response.json()
                reply = chat_response.get('reply', 'No reply')
                session_id = chat_response.get('session_id')
                response_time = chat_response.get('response_time_ms', 0)
                
                print(f"   ✅ AI Response received:")
                print(f"       Session: {session_id}")
                print(f"       Reply: {reply[:80]}...")
                print(f"       Response time: {response_time:.2f}ms")
                
                # Store session for cleanup
                if session_id:
                    self.session_id = session_id
                    
                return True
            else:
                print(f"   ❌ Chat failed: {response.status_code}")
                print(f"       Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Chat error: {e}")
            return False
    
    def test_ai_tool_usage(self) -> bool:
        """Test AI agent with tool usage"""
        print("\n🛠️ Testing AI Agent Tool Usage...")
        
        if not self.session_id:
            print("   ⚠️ No session available, skipping tool test")
            return False
        
        try:
            chat_payload = {
                "message": "¿Qué comunas tienes disponibles?",
                "session_id": self.session_id
            }
            response = requests.post(f"{self.base_url}/api/chat/message", json=chat_payload, timeout=25)
            
            if response.status_code == 200:
                chat_response = response.json()
                reply = chat_response.get('response', 'No response')
                tools_used = chat_response.get('tools_used', [])
                response_time = chat_response.get('response_time_ms', 0)
                
                print(f"   ✅ Tool-enabled response:")
                print(f"       Reply: {reply[:80]}...")
                print(f"       Tools used: {len(tools_used)}")
                print(f"       Response time: {response_time:.2f}ms")
                
                if tools_used:
                    for tool in tools_used:
                        print(f"         - {tool.get('tool')}: {tool.get('success', False)}")
                
                return True
            else:
                print(f"   ❌ Tool test failed: {response.status_code}")
                print(f"       Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Tool test error: {e}")
            return False
    
    def test_session_cleanup(self) -> bool:
        """Test session cleanup"""
        print("\n🧹 Testing Session Cleanup...")
        
        if not self.session_id:
            print("   ⚠️ No session to cleanup")
            return True
        
        try:
            response = requests.delete(f"{self.base_url}/api/chat/session/{self.session_id}", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Session {self.session_id} deleted successfully")
                self.session_id = None
                return True
            else:
                print(f"   ❌ Session cleanup failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Cleanup error: {e}")
            return False
    
    def run_full_test_suite(self):
        """Run complete test suite"""
        print("🚀 Spanish AI Agent API Test Suite")
        print("=" * 60)
        print(f"Testing server at: {self.base_url}")
        
        # Check server health first
        print("\n🏥 Checking Server Health...")
        if not self.test_server_health():
            print("❌ Server is not responding. Please start the server first.")
            print("   Run: uvicorn app.main:app --host 127.0.0.1 --port 8001")
            return False
        print("   ✅ Server is responding")
        
        # Run test suite
        results = []
        
        results.append(("Legacy Endpoints", self.test_legacy_endpoints()))
        results.append(("AI Session Creation", self.test_ai_session_creation()))
        results.append(("Simple AI Chat", self.test_ai_simple_chat()))
        results.append(("AI Tool Usage", self.test_ai_tool_usage()))
        results.append(("Session Cleanup", self.test_session_cleanup()))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Spanish AI Agent API is working perfectly!")
            return True
        else:
            print("⚠️ Some tests failed. Check the server logs for details.")
            return False

def main():
    """Main function"""
    # Allow custom server URL via command line
    base_url = "http://127.0.0.1:8001"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    tester = APITester(base_url)
    success = tester.run_full_test_suite()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
