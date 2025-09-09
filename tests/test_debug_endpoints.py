#!/usr/bin/env python3
"""
Test Debug Endpoints
Test the volume debug functionality before/after deployment
"""

import requests
import json
import time

def test_debug_endpoints(base_url):
    """Test all debug endpoints"""
    
    print(f"Testing Debug Endpoints: {base_url}")
    print("=" * 50)
    
    endpoints = [
        ("GET", "/admin/volume-debug", "Volume diagnostics"),
        ("GET", "/admin/database-status", "Database status"),
        ("GET", "/api/stats", "Basic statistics"),
        ("POST", "/admin/force-volume-update", "Force database update")
    ]
    
    results = {}
    
    for method, endpoint, description in endpoints:
        print(f"\n{description}...")
        print(f"{method} {endpoint}")
        
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=15)
            else:  # POST
                response = requests.post(f"{base_url}{endpoint}", timeout=30)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = data
                
                # Show key information based on endpoint
                if endpoint == "/admin/volume-debug":
                    debug_info = data.get('debug_info', {})
                    print(f"  Volume exists: {debug_info.get('volume_exists', 'unknown')}")
                    print(f"  Volume writable: {debug_info.get('volume_writable', 'unknown')}")
                    print(f"  Can write files: {debug_info.get('can_write_files', 'unknown')}")
                    print(f"  DB file exists: {debug_info.get('db_file_exists', 'unknown')}")
                    print(f"  DB connection: {debug_info.get('db_connection', 'unknown')}")
                    print(f"  Pharmacy count: {debug_info.get('pharmacy_count', 0)}")
                    
                elif endpoint == "/admin/database-status":
                    db_info = data.get('database_info', {})
                    print(f"  Pharmacy count: {db_info.get('pharmacy_count', 0)}")
                    print(f"  Age hours: {db_info.get('age_hours', 0):.1f}")
                    print(f"  Needs update: {db_info.get('needs_update', 'unknown')}")
                    
                elif endpoint == "/api/stats":
                    print(f"  Total pharmacies: {data.get('total_pharmacies', 0)}")
                    print(f"  Turno pharmacies: {data.get('turno_pharmacies', 0)}")
                    
                elif endpoint == "/admin/force-volume-update":
                    update_result = data.get('update_result', {})
                    final_state = data.get('final_state', {})
                    print(f"  Update successful: {update_result.get('updated', False)}")
                    print(f"  Final pharmacy count: {final_state.get('pharmacy_count', 0)}")
                    
            else:
                print(f"  ERROR: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                results[endpoint] = {"error": response.status_code, "text": response.text}
                
        except Exception as e:
            print(f"  FAILED: {e}")
            results[endpoint] = {"error": str(e)}
    
    # Summary
    print(f"\n" + "=" * 50)
    print("SUMMARY")
    print("-" * 20)
    
    success_count = sum(1 for r in results.values() if not isinstance(r, dict) or "error" not in r)
    total_count = len(endpoints)
    
    print(f"Successful endpoints: {success_count}/{total_count}")
    
    # Diagnose volume issues
    volume_debug = results.get("/admin/volume-debug", {})
    if isinstance(volume_debug, dict) and "debug_info" in volume_debug:
        debug_info = volume_debug["debug_info"]
        
        print(f"\nVOLUME DIAGNOSIS:")
        if not debug_info.get("volume_exists", False):
            print("  🚨 CRITICAL: Volume not mounted at /app/data")
        elif not debug_info.get("volume_writable", False):
            print("  🚨 CRITICAL: Volume not writable - permission issue")
        elif not debug_info.get("can_write_files", False):
            print("  🚨 CRITICAL: Cannot create files in volume")
        elif debug_info.get("pharmacy_count", 0) == 0:
            print("  ⚠️  WARNING: Database is empty - import may have failed")
        else:
            print("  ✅ SUCCESS: Volume and database appear healthy")
    
    return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter base URL (e.g., https://pharmacy-finder-debug.fly.dev): ").strip()
    
    if not url.startswith("http"):
        url = f"https://{url}"
    
    results = test_debug_endpoints(url)
    
    print(f"\nFull results saved to debug_results.json")
    with open("debug_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)