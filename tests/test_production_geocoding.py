#!/usr/bin/env python3
"""
Test reverse geocoding functionality with AI agent in production
"""
import requests
import json

def test_production_geocoding():
    """Test reverse geocoding with AI agent"""
    url = "https://pharmacy-finder-chile.fly.dev/chat"
    
    print("Testing Reverse Geocoding with AI Agent...")
    print("=" * 60)
    
    # Test 1: Villa Alemana coordinates (should detect location)
    print("\n1. Test: Villa Alemana GPS coordinates")
    print("   Query: 'farmacias cerca de -33.0443, -71.3744'")
    
    payload = {
        "message": "busco farmacias cerca de las coordenadas -33.0443, -71.3744"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   Status: Success {response.status_code}")
            print(f"   Response time: {result.get('response_time_ms', 0):.1f}ms")
            
            # Check geocoding results
            tool_results = result.get("tool_results", [])
            if tool_results:
                tool_data = tool_results[0].get("data", {}).get("data", {})
                resumen = tool_data.get("resumen", {})
                ubicacion = resumen.get("ubicacion_detectada", {})
                
                print(f"   Location detected: {ubicacion.get('descripcion', 'N/A')}")
                print(f"   Commune: {ubicacion.get('comuna', 'N/A')}")
                print(f"   Confidence: {ubicacion.get('confidence', 0.0):.2f}")
                print(f"   Method: {ubicacion.get('metodo', 'N/A')}")
                print(f"   Pharmacies found: {tool_data.get('total', 0)}")
                
                # Check if AI mentions the location in the response
                ai_reply = result.get("reply", "")
                location_mentioned = any(word in ai_reply.lower() for word in ["villa alemana", "alemana", "detecté", "ubicación"])
                print(f"   AI mentions location: {'Yes' if location_mentioned else 'No'}")
                
                # Show AI response (removing emojis to avoid encoding issues)
                ai_clean = ai_reply.encode('ascii', 'ignore').decode('ascii')
                ai_preview = ai_clean[:200] + "..." if len(ai_clean) > 200 else ai_clean
                print(f"   AI response: {ai_preview}")
            else:
                print("   No tool results found")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Santiago coordinates (should detect different location)
    print("\n2. Test: Santiago Centro GPS coordinates")
    print("   Query: 'farmacias cerca de -33.4489, -70.6693'")
    
    payload = {
        "message": "necesito farmacias cerca de las coordenadas -33.4489, -70.6693"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   Status: Success {response.status_code}")
            print(f"   Response time: {result.get('response_time_ms', 0):.1f}ms")
            
            # Check geocoding results
            tool_results = result.get("tool_results", [])
            if tool_results:
                tool_data = tool_results[0].get("data", {}).get("data", {})
                resumen = tool_data.get("resumen", {})
                ubicacion = resumen.get("ubicacion_detectada", {})
                
                print(f"   Location detected: {ubicacion.get('descripcion', 'N/A')}")
                print(f"   Commune: {ubicacion.get('comuna', 'N/A')}")
                print(f"   Confidence: {ubicacion.get('confidence', 0.0):.2f}")
                print(f"   Method: {ubicacion.get('metodo', 'N/A')}")
                print(f"   Pharmacies found: {tool_data.get('total', 0)}")
                
                # Check if AI mentions the detected location
                ai_reply = result.get("reply", "")
                detected_location = ubicacion.get('descripcion', '').lower()
                location_mentioned = detected_location in ai_reply.lower() if detected_location else False
                print(f"   AI mentions detected location: {'Yes' if location_mentioned else 'No'}")
                
                # Show AI response (removing emojis to avoid encoding issues)
                ai_clean = ai_reply.encode('ascii', 'ignore').decode('ascii')
                ai_preview = ai_clean[:200] + "..." if len(ai_clean) > 200 else ai_clean
                print(f"   AI response: {ai_preview}")
            else:
                print("   No tool results found")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Production geocoding test completed!")
    print("\nFeatures tested:")
    print("- Automatic commune detection from GPS coordinates")
    print("- AI agent integration with location awareness") 
    print("- User-friendly location messaging")
    print("- High accuracy local database geocoding")

if __name__ == "__main__":
    test_production_geocoding()