import requests
import json

def test_api_coordinates():
    """Test directo de la API con coordenadas"""
    
    url = "http://127.0.0.1:8001/chat"
    
    # Test 1: Mensaje en español con coordenadas
    payload1 = {
        "message": "Estoy en latitud -33.0485 y longitud -71.3700. Busca farmacias cerca.",
        "session_id": "test_api_coords"
    }
    
    print("🧪 Test 1: Coordenadas en mensaje")
    print(f"Mensaje: {payload1['message']}")
    
    try:
        response = requests.post(url, json=payload1, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📝 Respuesta: {result.get('response', 'No response')[:200]}...")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Mensaje con formato más directo
    payload2 = {
        "message": "Mi ubicación GPS: -33.0485, -71.3700. ¿Qué farmacias hay cerca?",
        "session_id": "test_api_coords2"
    }
    
    print("🧪 Test 2: Formato GPS")
    print(f"Mensaje: {payload2['message']}")
    
    try:
        response = requests.post(url, json=payload2, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📝 Respuesta: {result.get('response', 'No response')[:200]}...")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Testing API with Coordinates")
    print("=" * 60)
    test_api_coordinates()
    print("\n🏁 Test completed")
