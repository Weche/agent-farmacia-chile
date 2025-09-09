#!/usr/bin/env python3
"""
Test Deployment Script
Quick test of farmacias-chile-test deployment
"""

import requests
import time

def test_deployment():
    """Test the deployed debug app"""
    
    base_url = "https://farmacias-chile-test.fly.dev"
    
    print("Testing Deployment: farmacias-chile-test")
    print("=" * 45)
    print(f"URL: {base_url}")
    
    # Wait for deployment to be ready
    print("\n1. Testing basic connectivity...")
    
    for attempt in range(5):
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ App is responding!")
                health_data = response.json()
                print(f"   Environment: {health_data.get('env', 'unknown')}")
                break
            else:
                print(f"   Attempt {attempt+1}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   Attempt {attempt+1}: {e}")
            time.sleep(10)
    else:
        print("❌ App not responding after 5 attempts")
        return False
    
    # Test volume debug endpoint
    print("\n2. Testing volume debug...")
    try:
        response = requests.get(f"{base_url}/admin/volume-debug", timeout=15)
        if response.status_code == 200:
            data = response.json()
            debug_info = data.get('debug_info', {})
            
            print("✅ Volume debug successful!")
            print(f"   Volume exists: {debug_info.get('volume_exists', 'unknown')}")
            print(f"   Volume writable: {debug_info.get('volume_writable', 'unknown')}")
            print(f"   Can write files: {debug_info.get('can_write_files', 'unknown')}")
            print(f"   DB file exists: {debug_info.get('db_file_exists', 'unknown')}")
            print(f"   Pharmacy count: {debug_info.get('pharmacy_count', 0)}")
            
            return debug_info
        else:
            print(f"❌ Volume debug failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Volume debug error: {e}")
        return False

if __name__ == "__main__":
    result = test_deployment()
    if result:
        print(f"\n🎉 Test deployment successful!")
        print(f"Ready for full diagnosis at: https://farmacias-chile-test.fly.dev")
    else:
        print(f"\n❌ Test deployment needs investigation")