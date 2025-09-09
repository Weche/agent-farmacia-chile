#!/usr/bin/env python3
"""
Local Database Status Checker
Shows how the database update system works and current configuration
"""

import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def check_local_database_status():
    """Check local database status and update configuration"""
    
    print("Database Update System Status")
    print("=" * 40)
    
    try:
        from app.services.data_updater import DataUpdateService
        
        # Initialize the updater
        db_path = os.getenv('DATABASE_URL', 'pharmacy_finder.db')
        updater = DataUpdateService(db_path)
        
        print(f"Database path: {db_path}")
        print(f"Max age (hours): {updater.max_age_hours}")
        
        # Get database age info
        print(f"\nDATABASE STATUS")
        print("-" * 20)
        
        age_info = updater.get_database_age()
        
        if age_info.get('exists'):
            print(f"Database exists: YES")
            print(f"Pharmacy count: {age_info.get('pharmacy_count', 0)}")
            print(f"File modified: {age_info.get('file_modified')}")
            print(f"Age (hours): {age_info.get('age_hours', 0):.1f}")
            print(f"Is fresh: {'YES' if age_info.get('is_fresh') else 'NO'}")
            print(f"Needs update: {'YES' if age_info.get('needs_update') else 'NO'}")
            
            # Show update threshold
            max_hours = updater.max_age_hours
            current_age = age_info.get('age_hours', 0)
            
            print(f"\nUPDATE POLICY")
            print("-" * 15)
            print(f"Auto-update after: {max_hours} hours")
            print(f"Current age: {current_age:.1f} hours")
            
            if current_age >= max_hours:
                print("STATUS: Database will auto-update on next request")
            else:
                remaining = max_hours - current_age
                print(f"STATUS: Will auto-update in {remaining:.1f} hours")
                
        else:
            print("Database does not exist or cannot be accessed")
            print("Database will be created on first update")
            
        # Check environment configuration
        print(f"\nENVIRONMENT CONFIG")
        print("-" * 20)
        print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'pharmacy_finder.db')}")
        print(f"AUTO_UPDATE_DB_HOURS: {os.getenv('AUTO_UPDATE_DB_HOURS', '1')}")
        
        # Show how auto-updates are triggered
        print(f"\nAUTO-UPDATE TRIGGERS")
        print("-" * 22)
        print("Updates are triggered automatically when:")
        print("1. /api/chat endpoint is called (AI agent requests)")
        print("2. Database age exceeds the configured threshold")
        print("3. Database doesn't exist or has 0 pharmacies")
        print("4. Manual update via /admin/update-data endpoint")
        
        # Production vs local differences
        print(f"\nPRODUCTION vs LOCAL")
        print("-" * 21)
        print("Production configuration:")
        print("  DATABASE_URL: /app/data/pharmacy_finder.db (mounted volume)")
        print("  AUTO_UPDATE_DB_HOURS: 1 (updates every hour)")
        print("  Persistent storage: Fly.io volume 'pharmacy_data'")
        print("")
        print("Local configuration:")
        print("  DATABASE_URL: pharmacy_finder.db (local file)")
        print("  AUTO_UPDATE_DB_HOURS: 1 (or from .env)")
        print("  Storage: Local filesystem")
        
        print(f"\nSUMMARY")
        print("-" * 10)
        if updater.max_age_hours > 0:
            print("Auto-updates: ENABLED")
            print(f"Update frequency: Every {updater.max_age_hours} hour(s)")
            print("Trigger: AI agent requests + age check")
        else:
            print("Auto-updates: DISABLED")
            print("Manual updates only")
        
        print(f"\nProduction URL (corrected): https://pharmacy-finder-chile.fly.dev")
        print("Use this URL to check production status")
        
    except Exception as e:
        print(f"Error checking database status: {e}")
        import traceback
        traceback.print_exc()

def test_production_url():
    """Test the corrected production URL"""
    print(f"\nTEST PRODUCTION ACCESS")
    print("-" * 25)
    
    try:
        import requests
        
        # Test the corrected URL
        prod_url = "https://pharmacy-finder-chile.fly.dev"
        
        print(f"Testing: {prod_url}/api/stats")
        response = requests.get(f"{prod_url}/api/stats", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            print("SUCCESS: Production is accessible")
            print(f"Total pharmacies: {stats.get('total_pharmacies', 'unknown')}")
            print(f"Turno pharmacies: {stats.get('turno_pharmacies', 'unknown')}")
        else:
            print(f"HTTP Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Connection failed: {e}")
        print("Production may be down or URL incorrect")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        check_local_database_status()
        test_production_url()
    except KeyboardInterrupt:
        print("\nStatus check cancelled")
    except Exception as e:
        print(f"\nStatus check failed: {e}")
        import traceback
        traceback.print_exc()