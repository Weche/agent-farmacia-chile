"""
Quick Daily Data Quality Check
Simple check for monitoring daily data updates
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tests.test_data_quality import DataQualityChecker

def quick_check():
    """Run a quick daily check"""
    print("⚡ Quick Data Quality Check")
    print("=" * 30)
    
    checker = DataQualityChecker()
    
    # Check API availability (quick)
    api_results = checker.check_api_availability()
    api_ok = all("✅" in result['status'] for result in api_results.values())
    print(f"🌐 API Status: {'✅ OK' if api_ok else '❌ Issues'}")
    
    # Show API update dates
    for endpoint, result in api_results.items():
        if result['api_update_date']:
            endpoint_name = "Regular" if "Locales.php" in endpoint else "Turno"
            print(f"   {endpoint_name} API data: {result['api_update_date']}")
    
    # Check database freshness
    freshness = checker.check_database_freshness()
    print(f"📅 Data Freshness: {freshness['freshness_status']}")
    print(f"   Data update: {freshness['latest_update']} ({freshness['days_since_update']} days, {freshness['hours_since_update']} hours ago)")
    print(f"   DB file: {freshness['db_file_modified']}")
    
    # Quick stats
    stats = checker.db.get_pharmacy_count()
    print(f"📊 Quick Stats:")
    print(f"   Total: {stats['total']} | Turno: {stats['turno']} | Regular: {stats['regular']}")
    
    # Recommendation
    if isinstance(freshness['days_since_update'], int) and freshness['days_since_update'] > 2:
        print("\n💡 Recommendation: Consider running data import (python data/import_data.py)")
    elif not api_ok:
        print("\n💡 Note: API issues detected, but local data is fresh")
    else:
        print("\n✅ All systems looking good!")

if __name__ == "__main__":
    quick_check()
