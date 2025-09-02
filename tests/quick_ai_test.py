#!/usr/bin/env python3
"""
Quick AI Agent Test - Fast validation without server interference
"""
import requests
import time
import json

def quick_test():
    """Quick test of essential AI agent functionality"""
    print("🚀 Quick AI Agent Test")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:8001"
    
    try:
        # 1. Health Check
        print("1. Health Check...", end=" ")
        start = time.time()
        health = requests.get(f"{base_url}/api/stats", timeout=5)
        print(f"✅ OK ({(time.time()-start)*1000:.0f}ms)")
        
        # 2. Create Session
        print("2. Create Session...", end=" ")
        session_resp = requests.post(f"{base_url}/api/chat/session", timeout=10)
        session_id = session_resp.json()['session_id']
        print(f"✅ {session_id[:8]}...")
        
        # 3. Send Message
        print("3. Send AI Message...", end=" ")
        start = time.time()
        msg_resp = requests.post(
            f"{base_url}/api/chat/message?session_id={session_id}",
            json={"message": "Hola, busco farmacia en Santiago"},
            timeout=30
        )
        response_time = (time.time() - start) * 1000
        ai_response = msg_resp.json()
        print(f"✅ OK ({response_time:.0f}ms)")
        
        # Show AI response
        print(f"🤖 AI: {ai_response['response'][:80]}...")
        if ai_response.get('tools_used'):
            print(f"🔧 Tools: {', '.join(ai_response['tools_used'])}")
        
        # 4. Get History
        print("4. Get History...", end=" ")
        hist_resp = requests.get(f"{base_url}/api/chat/history/{session_id}", timeout=10)
        history = hist_resp.json()['conversation']
        print(f"✅ {len(history)} messages")
        
        # 5. Cleanup
        print("5. Cleanup...", end=" ")
        requests.delete(f"{base_url}/api/chat/session/{session_id}", timeout=10)
        print("✅ Done")
        
        print("\n🎉 Quick test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    quick_test()
