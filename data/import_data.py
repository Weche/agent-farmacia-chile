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
        backup_file = os.path.join(os.path.dirname(__file__), 'pharmacy_backup.json')
        
        try:
            if os.path.exists(backup_file):
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                if data_type == 'regular':
                    # Filter for regular pharmacies (not on duty)
                    return [item for item in backup_data.get('pharmacies', []) 
                           if len(item) > 12 and not item[12]]  # es_turno field
                elif data_type == 'turno':
                    # Filter for pharmacies on duty
                    return [item for item in backup_data.get('pharmacies', []) 
                           if len(item) > 12 and item[12]]  # es_turno field
                
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
