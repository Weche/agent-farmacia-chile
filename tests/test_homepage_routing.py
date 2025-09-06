#!/usr/bin/env python3
"""
🔄 HOMEPAGE ROUTING TEST
Test that main homepage now serves the modern interface
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8003"

def test_homepage_routing():
    """Test the updated homepage routing"""
    print("🔄 TESTING HOMEPAGE ROUTING CHANGES")
    print("=" * 50)
    
    tests = [
        ("/", "Main Homepage (should be modern now)"),
        ("/modern", "Modern endpoint (compatibility)"),
        ("/legacy", "Legacy homepage (original)"),
    ]
    
    results = []
    
    for endpoint, description in tests:
        print(f"\n📋 Testing: {description}")
        print("-" * 30)
        
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                content = response.text.lower()
                content_length = len(response.content)
                
                # Check for modern vs legacy indicators
                is_modern = any(indicator in content for indicator in [
                    'ai chat', 'spanish agent', 'chat-container', 
                    'modern', 'enhanced', 'assistant'
                ])
                
                is_legacy = any(indicator in content for indicator in [
                    'pharmacy finder', 'mvp v2', 'original'
                ]) and not is_modern
                
                has_chat = 'chat' in content and ('container' in content or 'interface' in content)
                
                print(f"✅ {description}")
                print(f"   📍 URL: {BASE_URL}{endpoint}")
                print(f"   🕐 Response Time: {response_time:.2f}ms")
                print(f"   📏 Content Length: {content_length:,} bytes")
                print(f"   🎨 Modern Features: {'✅' if is_modern else '❌'}")
                print(f"   💬 Chat Interface: {'✅' if has_chat else '❌'}")
                print(f"   📄 Page Type: {'Modern' if is_modern else 'Legacy' if is_legacy else 'Unknown'}")
                
                results.append({
                    "endpoint": endpoint,
                    "status": "✅",
                    "time": response_time,
                    "modern": is_modern,
                    "chat": has_chat,
                    "size": content_length
                })
                
            else:
                print(f"❌ {description}")
                print(f"   🚨 Status Code: {response.status_code}")
                results.append({
                    "endpoint": endpoint,
                    "status": "❌",
                    "time": response_time,
                    "modern": False,
                    "chat": False,
                    "size": 0
                })
                
        except Exception as e:
            print(f"❌ {description}")
            print(f"   🚨 Error: {str(e)}")
            results.append({
                "endpoint": endpoint,
                "status": "❌",
                "time": 0,
                "modern": False,
                "chat": False,
                "size": 0
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ROUTING CHANGE VERIFICATION")
    print("=" * 50)
    
    main_result = next((r for r in results if r["endpoint"] == "/"), None)
    modern_result = next((r for r in results if r["endpoint"] == "/modern"), None)
    legacy_result = next((r for r in results if r["endpoint"] == "/legacy"), None)
    
    if main_result and main_result["modern"]:
        print("✅ SUCCESS: Main homepage (/) now serves modern interface!")
        print(f"   📏 Content Size: {main_result['size']:,} bytes")
        print(f"   💬 Chat Interface: {'Present' if main_result['chat'] else 'Missing'}")
    else:
        print("❌ ISSUE: Main homepage is not serving modern interface")
    
    if modern_result and modern_result["status"] == "✅":
        print("✅ SUCCESS: /modern endpoint still works (compatibility)")
    else:
        print("⚠️  WARNING: /modern endpoint may have issues")
    
    if legacy_result and legacy_result["status"] == "✅":
        print("✅ SUCCESS: /legacy endpoint provides access to original interface")
    else:
        print("⚠️  INFO: /legacy endpoint not available")
    
    success_count = sum(1 for r in results if r["status"] == "✅")
    print(f"\n🎯 OVERALL: {success_count}/{len(results)} endpoints working")
    
    if success_count >= 2 and main_result and main_result["modern"]:
        print("🎉 ROUTING UPDATE SUCCESSFUL! Modern homepage is now default.")
    else:
        print("⚠️  Routing update may need attention.")

if __name__ == "__main__":
    test_homepage_routing()
