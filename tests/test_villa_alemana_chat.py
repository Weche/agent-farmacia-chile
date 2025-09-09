#!/usr/bin/env python3
"""
Test Villa Alemana pharmacy search via chat API
"""
import requests
import json
import sys

def test_villa_alemana_chat():
    """Test AI agent response to Villa Alemana query"""
    url = "https://pharmacy-finder-chile.fly.dev/chat"
    
    payload = {
        "message": "farmacias cerca de las coordenadas -33.0443, -71.3744"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Testing Villa Alemana chat query...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2, ensure_ascii=True))
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_villa_alemana_chat()