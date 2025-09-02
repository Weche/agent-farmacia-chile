#!/usr/bin/env python3
"""
Quick Health Check for Spanish AI Agent API
Simple, fast check that won't interfere with the server
"""

import requests
import sys
import time

def quick_health_check(base_url="http://127.0.0.1:8001"):
    """Quick health check of the API"""
    print(f"🏥 Quick Health Check: {base_url}")
    print("-" * 40)
    
    tests = [
        ("Server Response", lambda: requests.get(f"{base_url}/api/stats", timeout=5)),
        ("AI Agent Available", lambda: requests.post(f"{base_url}/api/chat/session", timeout=10)),
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            start_time = time.time()
            response = test_func()
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                print(f"✅ {test_name}: OK ({response_time:.0f}ms)")
            else:
                print(f"❌ {test_name}: Failed ({response.status_code})")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_name}: Error ({str(e)})")
            all_passed = False
    
    print("-" * 40)
    if all_passed:
        print("🎉 All systems operational!")
        return True
    else:
        print("⚠️ Some issues detected")
        return False

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
    success = quick_health_check(base_url)
    sys.exit(0 if success else 1)
