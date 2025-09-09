#!/usr/bin/env python3
"""
Test to verify the radius change from 5km to 10km is working
"""
import requests
import json

def test_radius_change():
    """Test different radius values to confirm 10km default"""
    
    # Test coordinates for Villa Alemana (where we know there are pharmacies)
    lat, lng = -33.0443, -71.3744
    
    print("Testing pharmacy search radius changes...")
    print("=" * 50)
    
    # Test 1: Default radius (should now be 10km)
    print(f"\n1. Testing DEFAULT radius (should be 10km now):")
    url = f"https://pharmacy-finder-chile.fly.dev/api/nearby?lat={lat}&lng={lng}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            default_count = len(data.get("farmacias", []))
            print(f"   Default radius: {default_count} pharmacies found")
        else:
            print(f"   Error: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Explicit 5km radius (should return fewer results)
    print(f"\n2. Testing EXPLICIT 5km radius:")
    url = f"https://pharmacy-finder-chile.fly.dev/api/nearby?lat={lat}&lng={lng}&radius=5.0"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            radius_5km_count = len(data.get("farmacias", []))
            print(f"   5km radius: {radius_5km_count} pharmacies found")
        else:
            print(f"   Error: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Explicit 10km radius (should match default)
    print(f"\n3. Testing EXPLICIT 10km radius:")
    url = f"https://pharmacy-finder-chile.fly.dev/api/nearby?lat={lat}&lng={lng}&radius=10.0"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            radius_10km_count = len(data.get("farmacias", []))
            print(f"   10km radius: {radius_10km_count} pharmacies found")
        else:
            print(f"   Error: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Analysis
    print(f"\nANALYSIS:")
    try:
        if 'default_count' in locals() and 'radius_5km_count' in locals() and 'radius_10km_count' in locals():
            print(f"   Default radius result: {default_count} pharmacies")
            print(f"   5km explicit result: {radius_5km_count} pharmacies")
            print(f"   10km explicit result: {radius_10km_count} pharmacies")
            
            if default_count == radius_10km_count:
                print("   SUCCESS: Default radius now matches 10km!")
            else:
                print("   ISSUE: Default radius doesn't match 10km")
                
            if default_count > radius_5km_count:
                print("   SUCCESS: Default finds more pharmacies than 5km")
            else:
                print("   ISSUE: Default doesn't find more than 5km")
        else:
            print("   Could not complete analysis due to API errors")
    except:
        print("   Error in analysis")

if __name__ == "__main__":
    test_radius_change()