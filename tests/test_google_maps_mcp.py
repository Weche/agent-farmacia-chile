#!/usr/bin/env python3
"""
Test script for Google Maps MCP integration
Run this to verify Google Maps tools are working correctly
"""

import asyncio
import os
import logging
from app.agents.tools.tool_registry import get_tool_registry

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_google_maps_tools():
    """Test Google Maps MCP tools"""
    
    print("🗺️ Testing Google Maps MCP Integration")
    print("=" * 50)
    
    # Check if Google Maps API key is configured
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key or api_key == "your_google_maps_api_key_here":
        print("❌ Google Maps API key not configured!")
        print("   Please set GOOGLE_MAPS_API_KEY in your .env file")
        print("   Get an API key from: https://console.cloud.google.com/")
        return
    
    # Get tool registry
    registry = get_tool_registry()
    
    # Test coordinates for Santiago, Chile
    test_lat = -33.4489
    test_lng = -70.6693
    test_address = "Providencia 123, Santiago, Chile"
    
    print(f"\n📍 Test coordinates: {test_lat}, {test_lng}")
    print(f"📍 Test address: {test_address}")
    
    # Test 1: Geocoding (Address to Coordinates)
    print("\n🔍 Test 1: Geocoding (Address to Coordinates)")
    try:
        result = await registry.execute_tool(
            "geocode_address",
            address=test_address,
            region="cl"
        )
        
        if result.get("success"):
            coords = result["data"]["coordinates"]
            formatted_addr = result["data"]["formatted_address"]
            print(f"   ✅ Success!")
            print(f"   📍 Coordinates: {coords['latitud']}, {coords['longitud']}")
            print(f"   📍 Formatted: {formatted_addr}")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Tool not available or error: {e}")
    
    # Test 2: Reverse Geocoding (Coordinates to Address)
    print("\n🔍 Test 2: Reverse Geocoding (Coordinates to Address)")
    try:
        result = await registry.execute_tool(
            "reverse_geocode",
            latitude=test_lat,
            longitude=test_lng
        )
        
        if result.get("success"):
            formatted_addr = result["data"]["formatted_address"]
            locality = result["data"].get("locality", "")
            print(f"   ✅ Success!")
            print(f"   📍 Address: {formatted_addr}")
            print(f"   🏢 Locality: {locality}")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Tool not available or error: {e}")
    
    # Test 3: Nearby Places (Find Pharmacies)
    print("\n🔍 Test 3: Nearby Places (Find Pharmacies)")
    try:
        result = await registry.execute_tool(
            "find_nearby_places",
            latitude=test_lat,
            longitude=test_lng,
            place_type="pharmacy",
            radius=2000,
            keyword="farmacia"
        )
        
        if result.get("success"):
            places = result["data"]["places"]
            total = result["data"]["total_results"]
            print(f"   ✅ Success!")
            print(f"   🏥 Found {total} nearby pharmacies")
            
            # Show first 3 results
            for i, place in enumerate(places[:3]):
                name = place["name"]
                vicinity = place["vicinity"]
                rating = place.get("rating", "No rating")
                print(f"   {i+1}. {name} - {vicinity} (⭐ {rating})")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Tool not available or error: {e}")
    
    # Test 4: Distance Matrix (Calculate Distances)
    print("\n🔍 Test 4: Distance Matrix (Calculate Travel Time)")
    try:
        # Test destinations around Santiago
        destinations = [
            {"lat": -33.4372, "lng": -70.6506},  # Las Condes
            {"lat": -33.4696, "lng": -70.6413},  # Ñuñoa
            {"lat": -33.4264, "lng": -70.6068}   # La Reina
        ]
        
        result = await registry.execute_tool(
            "calculate_distance_time",
            origin_lat=test_lat,
            origin_lng=test_lng,
            destinations=destinations,
            mode="driving"
        )
        
        if result.get("success"):
            results = result["data"]["results"]
            print(f"   ✅ Success!")
            print(f"   🚗 Travel times from origin:")
            
            for i, res in enumerate(results):
                if res["status"] == "OK":
                    distance = res["distance"]["text"]
                    duration = res["duration"]["text"]
                    print(f"   {i+1}. Distance: {distance}, Time: {duration}")
                else:
                    print(f"   {i+1}. Error: {res.get('error', 'Unknown')}")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Tool not available or error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Google Maps MCP Integration Test Complete!")
    
    # Show all available tools
    tools = registry.get_tool_names()
    google_tools = [t for t in tools if any(gm in t for gm in ["geocod", "places", "distance"])]
    
    print(f"\n📊 Available Google Maps Tools: {len(google_tools)}")
    for tool in google_tools:
        print(f"   - {tool}")
    
    print(f"\n📊 Total Tools in Registry: {len(tools)}")

if __name__ == "__main__":
    asyncio.run(test_google_maps_tools())
