#!/usr/bin/env python3
"""
Check Production Database Update Status
Monitors how often the production database is being updated
"""

import requests
import json
from datetime import datetime
import time

def check_production_db_status():
    """Check production database update frequency and status"""
    
    print("Production Database Status Checker")
    print("=" * 50)
    
    # Your production URL
    base_url = "https://mvp-farmacias-v2.fly.dev"
    
    endpoints_to_check = [
        "/admin/database-status",  # Database age and update info
        "/api/status",             # System status including data freshness
        "/api/data-freshness",     # Detailed freshness check
        "/api/stats"               # Database statistics
    ]
    
    print(f"Checking production database at: {base_url}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check database status
    try:
        print("1. DATABASE AGE & UPDATE STATUS")
        print("-" * 35)
        
        response = requests.get(f"{base_url}/admin/database-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if data.get('exists'):
                age_hours = data.get('age_hours', 0)
                pharmacy_count = data.get('pharmacy_count', 0)
                is_fresh = data.get('is_fresh', False)
                needs_update = data.get('needs_update', True)
                
                print(f"Database exists: YES")
                print(f"Pharmacy count: {pharmacy_count}")
                print(f"Database age: {age_hours:.1f} hours")
                print(f"Data is fresh: {'YES' if is_fresh else 'NO'}")
                print(f"Needs update: {'YES' if needs_update else 'NO'}")
                
                if data.get('file_modified'):
                    print(f"Last modified: {data['file_modified']}")
            else:
                print("Database does not exist or error accessing it")
        else:
            print(f"ERROR: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"ERROR checking database status: {e}")
    
    print()
    
    # Check system status
    try:
        print("2. SYSTEM STATUS & AUTO-UPDATE CONFIG")
        print("-" * 40)
        
        response = requests.get(f"{base_url}/api/status", timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            # Database component
            db_info = data.get('components', {}).get('database', {})
            db_status = db_info.get('status', 'unknown')
            
            print(f"Database status: {db_status}")
            print(f"Total pharmacies: {db_info.get('total_pharmacies', 'unknown')}")
            print(f"Turno pharmacies: {db_info.get('turno_pharmacies', 'unknown')}")
            
            if 'last_updated' in db_info:
                print(f"Last updated: {db_info['last_updated']}")
            
            if 'age_hours' in db_info:
                print(f"Data age: {db_info['age_hours']:.1f} hours")
                
            # Check if auto-updates are working
            auto_update_enabled = db_info.get('age_hours', 99) < 2  # Fresh if < 2 hours
            print(f"Auto-updates working: {'YES' if auto_update_enabled else 'NEEDS CHECK'}")
            
        else:
            print(f"ERROR: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"ERROR checking system status: {e}")
    
    print()
    
    # Check data freshness details
    try:
        print("3. DATA FRESHNESS ANALYSIS")
        print("-" * 30)
        
        response = requests.get(f"{base_url}/api/data-freshness", timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            freshness_info = data.get('freshness', {})
            overall_status = freshness_info.get('overall_status', 'unknown')
            status_icon = freshness_info.get('status_icon', '❓')
            
            print(f"Overall status: {overall_status} {status_icon}")
            
            if 'age_hours' in freshness_info:
                print(f"Data age: {freshness_info['age_hours']:.1f} hours")
                
            if 'last_update' in freshness_info:
                print(f"Last update: {freshness_info['last_update']}")
                
            # API endpoint status
            api_status = data.get('api_status', {})
            print(f"API endpoints health:")
            for endpoint, status in api_status.items():
                print(f"  {endpoint}: {status.get('status', 'unknown')}")
                
        else:
            print(f"ERROR: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"ERROR checking data freshness: {e}")
    
    print()
    
    # Check database statistics
    try:
        print("4. DATABASE STATISTICS")
        print("-" * 25)
        
        response = requests.get(f"{base_url}/api/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            
            print(f"Total pharmacies: {stats.get('total_pharmacies', 'unknown')}")
            print(f"Turno (24/7): {stats.get('turno_pharmacies', 'unknown')}")
            print(f"Regular: {stats.get('regular_pharmacies', 'unknown')}")
            print(f"Total communes: {stats.get('total_communes', 'unknown')}")
            
            if 'data_freshness' in stats:
                freshness = stats['data_freshness']
                print(f"Data freshness: {freshness}")
                
        else:
            print(f"ERROR: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"ERROR checking stats: {e}")
    
    print()
    print("5. RECOMMENDATIONS")
    print("-" * 20)
    
    # Based on the checks, provide recommendations
    print("Based on the status check above:")
    print("• If data age > 2 hours: Auto-updates may not be working")
    print("• If 'needs_update' = YES: Database should update soon")
    print("• Check logs in Fly.io dashboard for update errors")
    print("• Auto-update runs every hour (configurable via AUTO_UPDATE_DB_HOURS)")
    
    print(f"\n✅ Production database status check complete!")
    print(f"Run this script periodically to monitor update frequency")

if __name__ == "__main__":
    try:
        check_production_db_status()
    except KeyboardInterrupt:
        print("\nStatus check cancelled")
    except Exception as e:
        print(f"\nStatus check failed: {e}")
        import traceback
        traceback.print_exc()