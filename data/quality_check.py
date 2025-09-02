"""
Data Quality Monitor for Pharmacy Finder
This script checks the quality and freshness of pharmacy data
"""
import requests
from datetime import datetime, timedelta
from app.database import PharmacyDatabase
import sqlite3
import os

class DataQualityMonitor:
    """Monitor data quality and freshness"""
    
    def __init__(self):
        self.db = PharmacyDatabase()
        self.api_base = "https://midas.minsal.cl/farmacia_v2/WS"
    
    def check_api_status(self):
        """Check if MINSAL API is accessible and returning data"""
        print("🔍 Checking MINSAL API Status...")
        print("-" * 40)
        
        endpoints = {
            "Regular Pharmacies": "getLocales.php",
            "Turno Pharmacies": "getLocalesTurnos.php"
        }
        
        api_status = {}
        
        for name, endpoint in endpoints.items():
            url = f"{self.api_base}/{endpoint}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else 0
                    api_status[name] = {
                        "status": "✅ OK",
                        "count": count,
                        "url": url
                    }
                    print(f"{name}: ✅ OK ({count} records)")
                else:
                    api_status[name] = {
                        "status": f"❌ HTTP {response.status_code}",
                        "count": 0,
                        "url": url
                    }
                    print(f"{name}: ❌ HTTP {response.status_code}")
            except Exception as e:
                api_status[name] = {
                    "status": f"❌ Error: {str(e)}",
                    "count": 0,
                    "url": url
                }
                print(f"{name}: ❌ {str(e)}")
        
        return api_status
    
    def check_database_freshness(self):
        """Check how fresh our local database is"""
        print("\n📅 Checking Database Freshness...")
        print("-" * 40)
        
        # Check file modification time
        db_path = "pharmacy_finder.db"
        if os.path.exists(db_path):
            stat = os.stat(db_path)
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            hours_old = (datetime.now() - mod_time).total_seconds() / 3600
            
            print(f"Database file modified: {mod_time}")
            print(f"Hours since last update: {hours_old:.1f}")
            
            # Check data timestamps
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get latest update date from data
                cursor.execute("SELECT MAX(fecha_actualizacion) FROM pharmacies")
                latest_data = cursor.fetchone()[0]
                print(f"Latest data timestamp: {latest_data}")
                
                # Count records by update date
                cursor.execute("""
                    SELECT fecha_actualizacion, COUNT(*) 
                    FROM pharmacies 
                    GROUP BY fecha_actualizacion 
                    ORDER BY fecha_actualizacion DESC 
                    LIMIT 5
                """)
                recent_updates = cursor.fetchall()
                
                print("\nRecent update distribution:")
                for date, count in recent_updates:
                    print(f"  {date}: {count} records")
            
            # Freshness assessment
            if hours_old < 24:
                freshness = "🟢 Fresh (< 24 hours)"
            elif hours_old < 48:
                freshness = "🟡 Moderate (24-48 hours)"
            else:
                freshness = "🔴 Stale (> 48 hours)"
            
            print(f"\nFreshness Status: {freshness}")
            return freshness, hours_old
        else:
            print("❌ Database file not found!")
            return "❌ Missing", 0
    
    def check_data_completeness(self):
        """Check data quality and completeness"""
        print("\n🔍 Checking Data Completeness...")
        print("-" * 40)
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM pharmacies")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE es_turno = 1")
            turno_count = cursor.fetchone()[0]
            
            # Data quality checks
            cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE lat = 0 OR lng = 0")
            missing_coords = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE telefono IS NULL OR telefono = ''")
            missing_phone = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE direccion IS NULL OR direccion = ''")
            missing_address = cursor.fetchone()[0]
            
            # Geographic distribution
            cursor.execute("SELECT COUNT(DISTINCT comuna) FROM pharmacies")
            unique_communes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT region) FROM pharmacies")
            unique_regions = cursor.fetchone()[0]
            
            print(f"Total pharmacies: {total}")
            print(f"De turno: {turno_count}")
            print(f"Regular: {total - turno_count}")
            print(f"Geographic coverage: {unique_regions} regions, {unique_communes} communes")
            print(f"Missing coordinates: {missing_coords} ({missing_coords/total*100:.1f}%)")
            print(f"Missing phone: {missing_phone} ({missing_phone/total*100:.1f}%)")
            print(f"Missing address: {missing_address} ({missing_address/total*100:.1f}%)")
            
            # Data quality score
            coord_score = (total - missing_coords) / total * 100
            phone_score = (total - missing_phone) / total * 100
            address_score = (total - missing_address) / total * 100
            
            avg_score = (coord_score + phone_score + address_score) / 3
            
            if avg_score >= 90:
                quality = "🟢 Excellent"
            elif avg_score >= 75:
                quality = "🟡 Good"
            else:
                quality = "🔴 Needs improvement"
            
            print(f"\nData Quality Score: {avg_score:.1f}% - {quality}")
            
            return {
                "total": total,
                "turno": turno_count,
                "quality_score": avg_score,
                "missing_coords": missing_coords,
                "coverage": {"regions": unique_regions, "communes": unique_communes}
            }
    
    def suggest_actions(self, api_status, freshness_hours, data_quality):
        """Suggest actions based on checks"""
        print("\n💡 Recommendations...")
        print("-" * 40)
        
        actions = []
        
        # Check API availability
        api_working = all(status["status"].startswith("✅") for status in api_status.values())
        if not api_working:
            actions.append("🔧 Some API endpoints are not working - check network connectivity")
        
        # Check freshness
        if freshness_hours > 48:
            actions.append("🔄 Data is over 48 hours old - consider running data update")
        elif freshness_hours > 24:
            actions.append("⏰ Data is over 24 hours old - turno information may be outdated")
        
        # Check quality
        if data_quality["quality_score"] < 75:
            actions.append("📊 Data quality below 75% - investigate missing information")
        
        if data_quality["missing_coords"] > 100:
            actions.append("📍 Many pharmacies missing coordinates - may affect location search")
        
        if not actions:
            actions.append("✅ Everything looks good! No immediate action needed.")
        
        for action in actions:
            print(f"  {action}")
        
        return actions
    
    def run_full_check(self):
        """Run complete data quality check"""
        print("🏥 Pharmacy Finder - Data Quality Report")
        print("=" * 50)
        print(f"Report generated: {datetime.now()}")
        print()
        
        # Run all checks
        api_status = self.check_api_status()
        freshness, hours = self.check_database_freshness()
        quality = self.check_data_completeness()
        
        # Generate recommendations
        actions = self.suggest_actions(api_status, hours, quality)
        
        print("\n" + "=" * 50)
        print("Report completed!")
        
        return {
            "api_status": api_status,
            "freshness_hours": hours,
            "quality": quality,
            "actions": actions
        }

def main():
    """Run data quality check"""
    monitor = DataQualityMonitor()
    monitor.run_full_check()

if __name__ == "__main__":
    main()
