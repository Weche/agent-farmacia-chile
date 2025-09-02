"""
Data Quality Check for Pharmacy Finder
Tests data freshness, completeness, and API availability
"""
import requests
import sqlite3
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Add parent directory to path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import PharmacyDatabase

class DataQualityChecker:
    """Comprehensive data quality checker for pharmacy data"""
    
    def __init__(self):
        self.db = PharmacyDatabase()
        self.minsal_api_base = "https://midas.minsal.cl/farmacia_v2/WS"
        self.results = {}
    
    def check_api_availability(self) -> Dict:
        """Check if MINSAL API is responding and get update dates"""
        print("🌐 Checking MINSAL API availability...")
        
        api_status = {}
        endpoints = [
            "getLocales.php",
            "getLocalesTurnos.php"
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.minsal_api_base}/{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract API update date if available
                    api_update_date = None
                    if data and len(data) > 0 and 'fecha' in data[0]:
                        api_update_date = data[0]['fecha']
                    
                    api_status[endpoint] = {
                        "status": "✅ OK",
                        "response_time": response.elapsed.total_seconds(),
                        "data_count": len(data) if isinstance(data, list) else "N/A",
                        "api_update_date": api_update_date
                    }
                else:
                    api_status[endpoint] = {
                        "status": f"❌ Error {response.status_code}",
                        "response_time": None,
                        "data_count": 0,
                        "api_update_date": None
                    }
                    
            except Exception as e:
                api_status[endpoint] = {
                    "status": f"❌ Connection Error: {str(e)}",
                    "response_time": None,
                    "data_count": 0,
                    "api_update_date": None
                }
        
        return api_status
    
    def check_database_freshness(self) -> Dict:
        """Check how recent the database data is"""
        print("📅 Checking database freshness...")
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Get latest update date
            cursor.execute('SELECT MAX(fecha_actualizacion) FROM pharmacies')
            latest_update = cursor.fetchone()[0]
            
            # Get count by update date
            cursor.execute('''
                SELECT fecha_actualizacion, COUNT(*) 
                FROM pharmacies 
                GROUP BY fecha_actualizacion 
                ORDER BY fecha_actualizacion DESC 
                LIMIT 5
            ''')
            update_distribution = cursor.fetchall()
            
            # Get database file modification time (includes time)
            import os
            db_file_stat = os.stat(self.db.db_path)
            db_modified_time = datetime.fromtimestamp(db_file_stat.st_mtime)
            
            # Calculate days since last update
            if latest_update:
                try:
                    # Try different date formats
                    for date_format in ['%d-%m-%y', '%Y-%m-%d', '%d-%m-%Y']:
                        try:
                            latest_date = datetime.strptime(latest_update, date_format)
                            break
                        except ValueError:
                            continue
                    else:
                        # If no format worked, use current time
                        latest_date = datetime.now()
                        days_old = "Unknown date format"
                    
                    if isinstance(latest_date, datetime):
                        days_old = (datetime.now() - latest_date).days
                        hours_old = (datetime.now() - latest_date).total_seconds() / 3600
                except ValueError:
                    days_old = "Unknown format"
                    hours_old = "Unknown"
            else:
                days_old = "No date found"
                hours_old = "Unknown"
        
        return {
            "latest_update": latest_update,
            "days_since_update": days_old,
            "hours_since_update": round(hours_old, 1) if isinstance(hours_old, float) else hours_old,
            "db_file_modified": db_modified_time.strftime('%Y-%m-%d %H:%M:%S'),
            "update_distribution": update_distribution,
            "freshness_status": "✅ Fresh" if isinstance(days_old, int) and days_old <= 1 else "⚠️ Stale" if isinstance(days_old, int) and days_old <= 7 else "❌ Very Old"
        }
    
    def check_data_completeness(self) -> Dict:
        """Check data completeness and quality"""
        print("📊 Checking data completeness...")
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Total counts
            cursor.execute('SELECT COUNT(*) FROM pharmacies')
            total_pharmacies = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM pharmacies WHERE es_turno = 1')
            turno_count = cursor.fetchone()[0]
            
            # Missing data checks
            missing_checks = {}
            
            fields_to_check = [
                ('nombre', 'pharmacy names'),
                ('direccion', 'addresses'),
                ('comuna', 'communes'),
                ('telefono', 'phone numbers'),
                ('lat', 'latitude coordinates'),
                ('lng', 'longitude coordinates')
            ]
            
            for field, description in fields_to_check:
                if field in ['lat', 'lng']:
                    cursor.execute(f'SELECT COUNT(*) FROM pharmacies WHERE {field} = 0 OR {field} IS NULL')
                else:
                    cursor.execute(f'SELECT COUNT(*) FROM pharmacies WHERE {field} IS NULL OR {field} = ""')
                missing_count = cursor.fetchone()[0]
                missing_percentage = (missing_count / total_pharmacies * 100) if total_pharmacies > 0 else 0
                
                missing_checks[field] = {
                    "missing_count": missing_count,
                    "missing_percentage": round(missing_percentage, 2),
                    "status": "✅ Good" if missing_percentage < 5 else "⚠️ Warning" if missing_percentage < 20 else "❌ Critical"
                }
            
            # Geographic distribution
            cursor.execute('SELECT comuna, COUNT(*) FROM pharmacies GROUP BY comuna ORDER BY COUNT(*) DESC LIMIT 10')
            top_communes = cursor.fetchall()
            
        return {
            "total_pharmacies": total_pharmacies,
            "turno_count": turno_count,
            "missing_data": missing_checks,
            "top_communes": top_communes
        }
    
    def check_business_logic(self) -> Dict:
        """Check business logic and data consistency"""
        print("🔍 Checking business logic...")
        
        issues = []
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Check for pharmacies with invalid coordinates
            cursor.execute('SELECT COUNT(*) FROM pharmacies WHERE lat = 0 AND lng = 0')
            invalid_coords = cursor.fetchone()[0]
            if invalid_coords > 0:
                issues.append(f"❌ {invalid_coords} pharmacies with invalid coordinates (0,0)")
            
            # Check for pharmacies without proper hours
            cursor.execute('SELECT COUNT(*) FROM pharmacies WHERE hora_apertura IS NULL OR hora_cierre IS NULL')
            missing_hours = cursor.fetchone()[0]
            if missing_hours > 0:
                issues.append(f"⚠️ {missing_hours} pharmacies missing opening hours")
            
            # Check for duplicates (same name and address)
            cursor.execute('''
                SELECT nombre, direccion, COUNT(*) 
                FROM pharmacies 
                GROUP BY nombre, direccion 
                HAVING COUNT(*) > 1
            ''')
            duplicates = cursor.fetchall()
            if duplicates:
                issues.append(f"⚠️ {len(duplicates)} potential duplicate pharmacies")
            
            # Check turno percentage (should be reasonable)
            cursor.execute('SELECT COUNT(*) FROM pharmacies')
            total = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM pharmacies WHERE es_turno = 1')
            turno = cursor.fetchone()[0]
            turno_percentage = (turno / total * 100) if total > 0 else 0
            
            if turno_percentage < 1:
                issues.append(f"❌ Very low turno percentage: {turno_percentage:.1f}%")
            elif turno_percentage > 50:
                issues.append(f"❌ Suspiciously high turno percentage: {turno_percentage:.1f}%")
            else:
                issues.append(f"✅ Turno percentage looks normal: {turno_percentage:.1f}%")
        
        return {
            "issues": issues,
            "turno_percentage": turno_percentage
        }
    
    def run_full_check(self):
        """Run complete data quality check"""
        print("🏥 Pharmacy Finder - Data Quality Check")
        print("=" * 50)
        
        # API Availability
        api_results = self.check_api_availability()
        print("\n🌐 API Availability:")
        for endpoint, result in api_results.items():
            print(f"  {endpoint}: {result['status']}")
            if result['response_time']:
                print(f"    Response time: {result['response_time']:.2f}s")
                print(f"    Data count: {result['data_count']}")
                if result['api_update_date']:
                    print(f"    API data date: {result['api_update_date']}")
        
        # Database Freshness
        freshness_results = self.check_database_freshness()
        print(f"\n📅 Database Freshness: {freshness_results['freshness_status']}")
        print(f"  Latest data update: {freshness_results['latest_update']}")
        print(f"  Days since update: {freshness_results['days_since_update']}")
        print(f"  Hours since update: {freshness_results['hours_since_update']}")
        print(f"  DB file modified: {freshness_results['db_file_modified']}")
        print("  Recent updates:")
        for date, count in freshness_results['update_distribution']:
            print(f"    {date}: {count} pharmacies")
        
        # Data Completeness
        completeness_results = self.check_data_completeness()
        print(f"\n📊 Data Completeness:")
        print(f"  Total pharmacies: {completeness_results['total_pharmacies']}")
        print(f"  Turno pharmacies: {completeness_results['turno_count']}")
        print("  Missing data analysis:")
        for field, data in completeness_results['missing_data'].items():
            print(f"    {field}: {data['missing_count']} missing ({data['missing_percentage']}%) {data['status']}")
        
        print("\n🏙️ Top communes by pharmacy count:")
        for commune, count in completeness_results['top_communes']:
            print(f"    {commune}: {count} pharmacies")
        
        # Business Logic
        logic_results = self.check_business_logic()
        print(f"\n🔍 Business Logic Check:")
        for issue in logic_results['issues']:
            print(f"  {issue}")
        
        # Overall Status
        print(f"\n🎯 Overall Data Quality: ", end="")
        api_ok = all("✅" in result['status'] for result in api_results.values())
        freshness_ok = "✅" in freshness_results['freshness_status']
        completeness_ok = all(data['missing_percentage'] < 20 for data in completeness_results['missing_data'].values())
        
        if api_ok and freshness_ok and completeness_ok:
            print("✅ EXCELLENT")
        elif freshness_ok and completeness_ok:
            print("⚠️ GOOD (API issues)")
        elif freshness_ok or completeness_ok:
            print("⚠️ FAIR")
        else:
            print("❌ NEEDS ATTENTION")
        
        print("\n💡 Recommendations:")
        if not api_ok:
            print("  - Check MINSAL API connectivity")
        if not freshness_ok:
            print("  - Run data import to refresh pharmacy data")
        if not completeness_ok:
            print("  - Investigate missing data fields")
        
        return {
            "api": api_results,
            "freshness": freshness_results,
            "completeness": completeness_results,
            "business_logic": logic_results
        }

def main():
    """Main function to run data quality check"""
    checker = DataQualityChecker()
    results = checker.run_full_check()
    
    print(f"\n✅ Quality check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
