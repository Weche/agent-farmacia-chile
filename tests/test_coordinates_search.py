#!/usr/bin/env python3
"""
Test script para verificar la búsqueda de farmacias por coordenadas
"""

import requests
import json

def test_coordinates_search():
    """Test de búsqueda por coordenadas con ubicación específica"""
    
    # URL del endpoint de chat
    url = "http://127.0.0.1:8001/chat"
    
    # Coordenadas de Villa Alemana (donde debería haber farmacias)
    latitude = -33.0485
    longitude = -71.3700
    
    # Mensaje simulando que el usuario compartió su ubicación
    message = f"Mi ubicación es latitud {latitude}, longitud {longitude}. ¿Qué farmacias hay cerca?"
    
    payload = {
        "message": message,
        "session_id": "test_coordinates_session"
    }
    
    print(f"🧪 Probando búsqueda por coordenadas...")
    print(f"📍 Ubicación: {latitude}, {longitude}")
    print(f"💬 Mensaje: {message}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Respuesta exitosa:")
            print(f"📝 Respuesta del agente:")
            print(result.get('response', 'No response'))
            print("-" * 60)
            
            # Verificar si se usó la herramienta search_farmacias_nearby
            if 'farmacias' in result.get('response', '').lower():
                print("🎯 ¡La búsqueda por coordenadas funcionó!")
            else:
                print("⚠️  El agente respondió pero no está claro si encontró farmacias")
                
        else:
            print(f"❌ Error HTTP {response.status_code}:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error en la solicitud: {e}")

def test_direct_location_message():
    """Test con mensaje más directo sobre ubicación"""
    
    url = "http://127.0.0.1:8001/chat"
    
    # Mensaje más directo
    message = "Estoy en las coordenadas -33.0485, -71.3700. Busca farmacias cerca de aquí."
    
    payload = {
        "message": message,
        "session_id": "test_direct_location"
    }
    
    print(f"\n🧪 Probando con mensaje más directo...")
    print(f"💬 Mensaje: {message}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Respuesta exitosa:")
            print(f"📝 Respuesta del agente:")
            print(result.get('response', 'No response'))
            print("-" * 60)
            
        else:
            print(f"❌ Error HTTP {response.status_code}:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error en la solicitud: {e}")

if __name__ == "__main__":
    print("🔍 Testing Coordinates Search Functionality")
    print("=" * 60)
    
    # Test 1: Búsqueda por coordenadas
    test_coordinates_search()
    
    # Test 2: Mensaje más directo
    test_direct_location_message()
    
    print("\n🏁 Tests completados")
