#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE APP VERIFICATION TEST
Tests main website endpoints, status, and functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8003"
TIMEOUT = 10

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_test(test_name):
    """Print test name"""
    print(f"\n📋 {test_name}")
    print("-" * 40)

def test_main_website():
    """Test the main website endpoints"""
    print_test("MAIN WEBSITE ENDPOINTS")
    
    endpoints_to_test = [
        ("/", "Main homepage (original)"),
        ("/modern", "Modern homepage"), 
        ("/status", "Status page"),
        ("/docs", "API documentation"),
    ]
    
    results = []
    
    for endpoint, description in endpoints_to_test:
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
            response_time = (time.time() - start_time) * 1000
            
            # Check response
            if response.status_code == 200:
                content_length = len(response.content)
                content_type = response.headers.get('content-type', 'unknown')
                
                print(f"✅ {description}")
                print(f"   📍 URL: {BASE_URL}{endpoint}")
                print(f"   🕐 Response Time: {response_time:.2f}ms")
                print(f"   📄 Content Type: {content_type}")
                print(f"   📏 Content Length: {content_length:,} bytes")
                
                # Special checks for HTML pages
                if 'text/html' in content_type:
                    content = response.text.lower()
                    has_title = '<title>' in content
                    has_css = 'css' in content or 'stylesheet' in content
                    has_js = 'javascript' in content or '.js' in content
                    
                    print(f"   🎨 HTML Features: Title:{has_title}, CSS:{has_css}, JS:{has_js}")
                
                results.append({"endpoint": endpoint, "status": "✅", "time": response_time})
            else:
                print(f"❌ {description}")
                print(f"   📍 URL: {BASE_URL}{endpoint}")
                print(f"   🚨 Status Code: {response.status_code}")
                print(f"   📝 Error: {response.text[:200]}...")
                results.append({"endpoint": endpoint, "status": "❌", "time": response_time})
                
        except Exception as e:
            print(f"❌ {description}")
            print(f"   📍 URL: {BASE_URL}{endpoint}")
            print(f"   🚨 Error: {str(e)}")
            results.append({"endpoint": endpoint, "status": "❌", "time": 0})
    
    return results

def test_api_endpoints():
    """Test core API endpoints"""
    print_test("API ENDPOINTS")
    
    api_endpoints = [
        ("/api/stats", "Statistics API"),
        ("/api/communes", "Communes list API"),
        ("/api/search?comuna=santiago", "Search API (Santiago)"),
    ]
    
    results = []
    
    for endpoint, description in api_endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ {description}")
                    print(f"   📍 URL: {BASE_URL}{endpoint}")
                    print(f"   🕐 Response Time: {response_time:.2f}ms")
                    
                    # Analyze JSON response
                    if isinstance(data, dict):
                        key_count = len(data.keys())
                        print(f"   📊 JSON Keys: {key_count} ({', '.join(list(data.keys())[:5])}{'...' if key_count > 5 else ''})")
                        
                        # Special handling for search results
                        if 'locales' in data:
                            pharmacy_count = len(data.get('locales', []))
                            print(f"   🏥 Pharmacies Found: {pharmacy_count}")
                            
                    elif isinstance(data, list):
                        print(f"   📊 Array Items: {len(data)}")
                        
                    results.append({"endpoint": endpoint, "status": "✅", "time": response_time})
                    
                except json.JSONDecodeError:
                    print(f"❌ {description} - Invalid JSON response")
                    results.append({"endpoint": endpoint, "status": "❌", "time": response_time})
            else:
                print(f"❌ {description}")
                print(f"   🚨 Status Code: {response.status_code}")
                results.append({"endpoint": endpoint, "status": "❌", "time": response_time})
                
        except Exception as e:
            print(f"❌ {description}")
            print(f"   🚨 Error: {str(e)}")
            results.append({"endpoint": endpoint, "status": "❌", "time": 0})
    
    return results

def test_chat_api():
    """Test Spanish AI Agent chat functionality"""
    print_test("SPANISH AI AGENT CHAT")
    
    results = []
    
    # Test simple chat endpoint
    try:
        print("1️⃣ Testing simple chat endpoint...")
        start_time = time.time()
        
        chat_payload = {
            "message": "Hola, busco farmacias en Las Condes"
        }
        
        response = requests.post(f"{BASE_URL}/chat", json=chat_payload, timeout=30)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Chat Response Received")
            print(f"   🕐 Response Time: {response_time:.2f}ms")
            print(f"   🆔 Session ID: {data.get('session_id', 'N/A')}")
            print(f"   🤖 Reply Length: {len(data.get('reply', ''))} characters")
            print(f"   🛠️  Tools Used: {len(data.get('tools_used', []))}")
            print(f"   💬 Preview: {data.get('reply', '')[:100]}...")
            
            results.append({"test": "simple_chat", "status": "✅", "time": response_time})
        else:
            print(f"   ❌ Chat failed: {response.status_code}")
            print(f"   📝 Error: {response.text[:200]}")
            results.append({"test": "simple_chat", "status": "❌", "time": response_time})
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        results.append({"test": "simple_chat", "status": "❌", "time": 0})
    
    return results

def test_status_endpoint_detailed():
    """Detailed test of the /status endpoint"""
    print_test("STATUS ENDPOINT DETAILED ANALYSIS")
    
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/status", timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000
        
        print(f"📍 URL: {BASE_URL}/status")
        print(f"🕐 Response Time: {response_time:.2f}ms")
        print(f"📋 Status Code: {response.status_code}")
        print(f"📄 Content Type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            content = response.text
            content_length = len(content)
            print(f"📏 Content Length: {content_length:,} bytes")
            
            # Check for key elements in status page
            checks = {
                "HTML structure": "<html" in content.lower(),
                "Title tag": "<title>" in content.lower(),
                "Status info": "status" in content.lower(),
                "System info": any(keyword in content.lower() for keyword in ["system", "health", "version", "uptime"]),
                "Styling": any(keyword in content.lower() for keyword in ["css", "style", "stylesheet"]),
            }
            
            print("\n🔍 Content Analysis:")
            for check, result in checks.items():
                print(f"   {'✅' if result else '❌'} {check}: {result}")
            
            return {"status": "✅", "time": response_time, "checks": checks}
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return {"status": "❌", "time": response_time, "checks": {}}
            
    except Exception as e:
        print(f"❌ Error accessing status endpoint: {str(e)}")
        return {"status": "❌", "time": 0, "checks": {}}

def test_server_health():
    """Test overall server health"""
    print_test("SERVER HEALTH CHECK")
    
    try:
        # Test basic connectivity
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/", timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        server_responsive = response.status_code == 200
        
        print(f"🌐 Server Connectivity: {'✅ OK' if server_responsive else '❌ Failed'}")
        print(f"🕐 Base Response Time: {response_time:.2f}ms")
        
        if server_responsive:
            # Check server headers
            server_header = response.headers.get('server', 'Unknown')
            print(f"🖥️  Server: {server_header}")
            
            # Check if it's our FastAPI app
            is_fastapi = 'uvicorn' in server_header.lower() or 'fastapi' in response.headers.get('x-powered-by', '').lower()
            print(f"⚡ FastAPI Detected: {'✅' if is_fastapi else '❓'}")
            
        return {"responsive": server_responsive, "time": response_time}
        
    except Exception as e:
        print(f"❌ Server health check failed: {str(e)}")
        return {"responsive": False, "time": 0}

def generate_summary_report(website_results, api_results, chat_results, status_result, health_result):
    """Generate a summary report"""
    print_header("SUMMARY REPORT")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"📅 Test Completed: {timestamp}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Count successes
    website_success = sum(1 for r in website_results if r["status"] == "✅")
    api_success = sum(1 for r in api_results if r["status"] == "✅")
    chat_success = sum(1 for r in chat_results if r["status"] == "✅")
    
    total_tests = len(website_results) + len(api_results) + len(chat_results) + 2  # +2 for status and health
    total_success = website_success + api_success + chat_success
    total_success += (1 if status_result["status"] == "✅" else 0)
    total_success += (1 if health_result["responsive"] else 0)
    
    success_rate = (total_success / total_tests) * 100
    
    print(f"\n📊 RESULTS:")
    print(f"   🌐 Website Endpoints: {website_success}/{len(website_results)} ✅")
    print(f"   🔌 API Endpoints: {api_success}/{len(api_results)} ✅")
    print(f"   🤖 Chat Functionality: {chat_success}/{len(chat_results)} ✅")
    print(f"   📋 Status Page: {'✅' if status_result['status'] == '✅' else '❌'}")
    print(f"   🏥 Server Health: {'✅' if health_result['responsive'] else '❌'}")
    
    print(f"\n🎯 OVERALL SUCCESS RATE: {success_rate:.1f}% ({total_success}/{total_tests})")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT! System is fully operational")
    elif success_rate >= 75:
        print("👍 GOOD! System is mostly working with minor issues")
    elif success_rate >= 50:
        print("⚠️  FAIR! System has some issues that need attention")
    else:
        print("🚨 POOR! System has major issues requiring immediate attention")
    
    # Average response times
    all_times = [r["time"] for r in website_results + api_results + chat_results if r["time"] > 0]
    if all_times:
        avg_time = sum(all_times) / len(all_times)
        print(f"⚡ Average Response Time: {avg_time:.2f}ms")

def main():
    """Run all tests"""
    print_header("COMPREHENSIVE APP VERIFICATION")
    print(f"🎯 Testing application at: {BASE_URL}")
    
    # Run all tests
    health_result = test_server_health()
    
    if not health_result["responsive"]:
        print("\n🚨 Server not responsive. Cannot continue with tests.")
        print("👉 Make sure the application is running:")
        print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload")
        sys.exit(1)
    
    website_results = test_main_website()
    api_results = test_api_endpoints()
    chat_results = test_chat_api()
    status_result = test_status_endpoint_detailed()
    
    # Generate summary
    generate_summary_report(website_results, api_results, chat_results, status_result, health_result)
    
    print(f"\n✅ Test completed successfully!")

if __name__ == "__main__":
    main()
