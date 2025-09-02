#!/usr/bin/env python3
"""
Test simple para verificar respuesta del chat
"""

import requests
import json

def test_chat_response():
    print("🧪 Testing chat response structure...")
    
    payload = {
        'message': 'Estoy en las coordenadas -33.0381, -71.3852. Busca farmacias cerca',
        'session_id': 'test_map_debug'
    }
    
    try:
        response = requests.post('http://127.0.0.1:8001/chat', json=payload, timeout=30)
        print(f'✅ Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'📋 Response keys: {list(data.keys())}')
            
            # Check for tool_results
            if 'tool_results' in data:
                print(f'🔧 Tool results found: {len(data["tool_results"])} tools')
                for i, tool in enumerate(data['tool_results']):
                    print(f'   Tool {i+1}: {tool.get("tool", "unknown")}')
                    print(f'   Success: {tool.get("success", False)}')
                    if tool.get('data') and 'farmacias' in tool['data']:
                        farmacias = tool['data']['farmacias']
                        print(f'   Pharmacies: {len(farmacias)}')
                        for farmacia in farmacias[:2]:
                            print(f'     - {farmacia["nombre"]} at {farmacia.get("ubicacion", "No coords")}')
            else:
                print('❌ No tool_results in response')
                
        else:
            print(f'❌ Error: {response.text}')
            
    except Exception as e:
        print(f'❌ Exception: {e}')

if __name__ == "__main__":
    test_chat_response()
