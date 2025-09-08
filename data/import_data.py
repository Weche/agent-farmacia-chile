"""
Data import script for MINSAL pharmacy data
"""
import requests
import os
import sys
from dotenv import load_dotenv
from typing import List, Dict
import time
import json

# Add parent directory to path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import Pharmacy, PharmacyDatabase

# Load environment variables
load_dotenv()
MINSAL_API_BASE = os.getenv("MINSAL_API_BASE", "https://midas.minsal.cl/farmacia_v2/WS")

class MINSALDataImporter:
    """Import pharmacy data from MINSAL API"""

    def __init__(self, db: PharmacyDatabase):
        self.db = db
        self.api_base = MINSAL_API_BASE

    def fetch_api_data(self, endpoint: str) -> List[Dict]:
        """Fetch data from MINSAL API with retry logic"""
        url = f"{self.api_base}/{endpoint}"
        print(f"📡 Fetching from: {url}")

        # Add headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.minsal.cl/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        }

        # Try multiple times with different approaches
        for attempt in range(3):
            try:
                print(f"   Attempt {attempt + 1}/3...")
                
                # Try with different timeout and headers
                if attempt == 1:
                    headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                elif attempt == 2:
                    # Try without some headers that might be causing issues
                    headers.pop('Sec-Fetch-Dest', None)
                    headers.pop('Sec-Fetch-Mode', None)
                    headers.pop('Sec-Fetch-Site', None)
                    headers.pop('Sec-Ch-Ua', None)
                    headers.pop('Sec-Ch-Ua-Mobile', None)
                    headers.pop('Sec-Ch-Ua-Platform', None)
                
                resp = requests.get(url, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'data' in data:
                    return data['data']
                else:
                    print(f"⚠️  Unexpected data format: {type(data)}")
                    return []

            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(2)  # Wait before retry
                continue

        print(f"❌ All attempts failed for {endpoint}")
        return []

    def import_all_pharmacies(self):
        """Import all pharmacy data with fallback to backup"""
        print("🏥 Starting pharmacy data import...")
        print("=" * 50)

        # Import regular pharmacies
        print("\n📋 Importing regular pharmacies...")
        regular_data = self.fetch_api_data("getLocales.php")
        
        if not regular_data:
            print("⚠️  API failed, trying backup data...")
            regular_data = self.load_backup_data('regular')
        
        if regular_data:
            pharmacies = [Pharmacy.from_api_data(item, es_turno=False)
                         for item in regular_data]
            self.db.save_multiple_pharmacies(pharmacies)
            print(f"✅ Saved {len(pharmacies)} regular pharmacies")

        # Import pharmacies on duty
        print("\n⏰ Importing pharmacies on duty...")
        turno_data = self.fetch_api_data("getLocalesTurnos.php")
        
        if not turno_data:
            print("⚠️  API failed, trying backup data...")
            turno_data = self.load_backup_data('turno')
        
        if turno_data:
            turno_pharmacies = [Pharmacy.from_api_data(item, es_turno=True)
                              for item in turno_data]
            self.db.save_multiple_pharmacies(turno_pharmacies)
            print(f"✅ Saved {len(turno_pharmacies)} pharmacies on duty")

        # Show statistics
        stats = self.db.get_pharmacy_count()
        print("\n📊 Database Statistics:")
        print(f"   Total pharmacies: {stats['total']}")
        print(f"   On duty: {stats['turno']}")
        print(f"   Regular: {stats['regular']}")

        # Show sample communes
        communes = self.db.get_all_communes()
        print(f"\n🏙️  Available communes: {len(communes)}")
        print("Sample communes:", communes[:10])

    def load_backup_data(self, data_type: str) -> List[Dict]:
        """Load backup data when API fails"""
        # Try multiple locations for backup file
        backup_locations = [
            os.path.join(os.path.dirname(__file__), 'pharmacy_backup.json'),
            '/app/data_source/pharmacy_backup.json',  # Container source location
            '/app/data/pharmacy_backup.json',  # Volume location
        ]
        
        backup_file = None
        for location in backup_locations:
            if os.path.exists(location):
                backup_file = location
                print(f"🔍 Found backup file at: {backup_file}")
                break
        
        if not backup_file:
            print(f"❌ No backup file found in locations: {backup_locations}")
            return []
        
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
                
            pharmacies = []
            for item in backup_data.get('pharmacies', []):
                # Expect at least 14 fields (index 0..13), where index 13 is es_turno
                if len(item) < 14:
                    continue
                
                # Convert list to dict format expected by Pharmacy.from_api_data
                # Keys aligned to app.database.Pharmacy.from_api_data expectations
                pharmacy_dict = {
                    'local_id': str(item[0]),
                    'local_nombre': item[1],
                    'local_direccion': item[2],
                    'comuna_nombre': item[3],
                    'localidad_nombre': item[4],
                    'fk_region': item[5],
                    'local_telefono': item[6],
                    'local_lat': str(item[7]),
                    'local_lng': str(item[8]),
                    'funcionamiento_hora_apertura': item[9],
                    'funcionamiento_hora_cierre': item[10],
                    'funcionamiento_dia': item[11],
                    'fecha': item[12]
                }
                
                # Filter by type
                try:
                    es_turno = int(item[13])
                except (ValueError, TypeError):
                    # If parsing fails, skip this row to avoid misclassification
                    continue

                if data_type == 'regular' and es_turno == 0:
                    pharmacies.append(pharmacy_dict)
                elif data_type == 'turno' and es_turno == 1:
                    pharmacies.append(pharmacy_dict)
            
            return pharmacies
                
        except Exception as e:
            print(f"❌ Error loading backup data: {e}")
        
        return []

    def test_villa_alemana(self):
        """Test search for Villa Alemana"""
        print("\n🏥 Testing Villa Alemana search...")
        pharmacies = self.db.find_by_comuna("villa alemana", only_open=True)

        if pharmacies:
            print(f"✅ Found {len(pharmacies)} pharmacies in Villa Alemana:")
            for i, pharmacy in enumerate(pharmacies[:5], 1):
                print(f"   {i}. {pharmacy.nombre}")
                print(f"      📍 {pharmacy.direccion}")
                print(f"      📞 {pharmacy.telefono or 'No phone'}")
                print(f"      🕐 {pharmacy.hora_apertura} - {pharmacy.hora_cierre}")
                print(f"      📌 {pharmacy.lat}, {pharmacy.lng}")
                print()
        else:
            print("❌ No pharmacies found in Villa Alemana")

def main():
    """Main import function"""
    print("💊 Pharmacy Finder - Data Import")
    print("=" * 40)

    # Initialize database
    db = PharmacyDatabase()

    # Create importer
    importer = MINSALDataImporter(db)

    # Import data
    importer.import_all_pharmacies()

    # Test specific location
    importer.test_villa_alemana()

    print("\n✅ Data import completed!")
    print("💡 You can now run the web interface to explore the data.")

if __name__ == "__main__":
    main()
