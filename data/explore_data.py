import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MINSAL_API_BASE = os.getenv("MINSAL_API_BASE", "https://midas.minsal.cl/farmacia_v2/WS")

def explore_minsal_data():
    """Explore the MINSAL API data structure"""
    print("🔍 Exploring MINSAL Pharmacy Data")
    print("=" * 50)

    # Test different endpoints
    endpoints = [
        "getLocales.php",
        "getLocalesTurnos.php"
    ]

    for endpoint in endpoints:
        print(f"\n📊 Testing endpoint: {endpoint}")
        try:
            url = f"{MINSAL_API_BASE}/{endpoint}"
            print(f"URL: {url}")

            resp = requests.get(url, timeout=15)
            print(f"Status: {resp.status_code}")

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"Data type: {type(data)}")

                    if isinstance(data, list) and len(data) > 0:
                        print(f"Records found: {len(data)}")
                        print("\n📋 Sample record structure:")
                        sample = data[0]
                        for key, value in sample.items():
                            print(f"  {key}: {type(value).__name__} = {str(value)[:50]}...")

                        print("\n🔍 Available fields:")
                        print(f"  {list(sample.keys())}")

                        # Check for location data
                        has_location = 'local_lat' in sample and 'local_lng' in sample
                        print(f"📍 Has location data: {has_location}")

                        if has_location:
                            valid_coords = 0
                            for item in data[:10]:  # Check first 10
                                lat = item.get('local_lat')
                                lng = item.get('local_lng')
                                if lat and lng and lat != '0' and lng != '0':
                                    valid_coords += 1
                            print(f"📍 Valid coordinates in sample: {valid_coords}/10")

                    elif isinstance(data, dict):
                        print(f"Dictionary keys: {list(data.keys())}")
                        if 'data' in data:
                            print(f"Data array length: {len(data['data'])}")

                except json.JSONDecodeError:
                    print("❌ Response is not valid JSON")
                    print(f"Raw response: {resp.text[:200]}...")

            else:
                print(f"❌ HTTP Error: {resp.status_code}")
                print(f"Response: {resp.text[:200]}...")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    explore_minsal_data()
