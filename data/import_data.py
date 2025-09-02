"""
Data import script for MINSAL pharmacy data
"""
import requests
import os
import sys
from dotenv import load_dotenv
from typing import List, Dict
import time

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
        """Fetch data from MINSAL API"""
        url = f"{self.api_base}/{endpoint}"
        print(f"📡 Fetching from: {url}")

        try:
            resp = requests.get(url, timeout=30)
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
            print(f"❌ Error fetching {endpoint}: {e}")
            return []

    def import_all_pharmacies(self):
        """Import all pharmacy data"""
        print("🏥 Starting pharmacy data import...")
        print("=" * 50)

        # Import regular pharmacies
        print("\n📋 Importing regular pharmacies...")
        regular_data = self.fetch_api_data("getLocales.php")
        if regular_data:
            pharmacies = [Pharmacy.from_api_data(item, es_turno=False)
                         for item in regular_data]
            self.db.save_multiple_pharmacies(pharmacies)
            print(f"✅ Saved {len(pharmacies)} regular pharmacies")

        # Import pharmacies on duty
        print("\n⏰ Importing pharmacies on duty...")
        turno_data = self.fetch_api_data("getLocalesTurnos.php")
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
