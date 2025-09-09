#!/usr/bin/env python3
"""
Test the intelligent radius expansion with the AI agent in production
"""
import requests
import json

def test_radius_expansion_agent():
    """Test AI agent response with radius expansion"""
    url = "https://pharmacy-finder-chile.fly.dev/chat"
    
    # Test 1: Rural coordinates that should trigger expansion
    print("Testing radius expansion with AI agent...")
    print("=" * 60)
    
    print("\n1. Test: Rural coordinates (should expand automatically)")
    print("   Query: 'farmacias cerca de -34.5000, -71.0000'")
    
    payload = {
        "message": "farmacias cerca de las coordenadas -34.5000, -71.0000"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   Status: Success {response.status_code}")
            print(f"   Response time: {result.get('response_time_ms', 0):.1f}ms")
            
            # Check if radius expansion was used
            tool_results = result.get("tool_results", [])
            if tool_results:
                tool_data = tool_results[0].get("data", {}).get("data", {})
                resumen = tool_data.get("resumen", {})
                
                print(f"   Radius inicial: {resumen.get('radio_inicial', 'N/A')}km")
                print(f"   Radius final: {resumen.get('radio_km', 'N/A')}km")
                print(f"   Expansion occurred: {resumen.get('radio_expandido', False)}")
                print(f"   Pharmacies found: {tool_data.get('total', 0)}")
                
                # Print part of the AI response
                ai_reply = result.get("reply", "")[:200] + "..." if len(result.get("reply", "")) > 200 else result.get("reply", "")
                print(f"   AI response preview: {ai_reply}")
            else:
                print("   No tool results found")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Urban coordinates (Villa Alemana - should not need expansion)
    print("\n2. Test: Urban coordinates (should find results quickly)")
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
            
            # Check radius expansion
            tool_results = result.get("tool_results", [])
            if tool_results:
                tool_data = tool_results[0].get("data", {}).get("data", {})
                resumen = tool_data.get("resumen", {})
                
                print(f"   Radius inicial: {resumen.get('radio_inicial', 'N/A')}km")
                print(f"   Radius final: {resumen.get('radio_km', 'N/A')}km")
                print(f"   Expansion occurred: {resumen.get('radio_expandido', False)}")
                print(f"   Pharmacies found: {tool_data.get('total', 0)}")
                
                ai_reply = result.get("reply", "")[:200] + "..." if len(result.get("reply", "")) > 200 else result.get("reply", "")
                print(f"   AI response preview: {ai_reply}")
            else:
                print("   No tool results found")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Production radius expansion test completed!")

if __name__ == "__main__":
    test_radius_expansion_agent()