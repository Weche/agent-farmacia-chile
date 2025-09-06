"""
Test Corregido - Enlaces Clickeables con rutas correctas
"""

import requests
import json

def test_corrected_api():
    """Test con las rutas correctas de la API"""
    print("🔍 TEST API CORREGIDO")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8003"
    
    # Test 1: Nuevo endpoint simple
    print("\n1. Test endpoint simple /api/chat:")
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": "emergencia maipu direcciones"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📝 Message length: {len(message)}")
            print(f"   🔗 Contains [text](url): {'[' in message and '](' in message}")
            print(f"   📄 Preview: {message[:150]}...")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Endpoint de testing directo
    print("\n2. Test endpoint directo /test-links:")
    try:
        response = requests.get(f"{base_url}/test-links")
        if response.status_code == 200:
            html_content = response.text
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 HTML length: {len(html_content)}")
            print(f"   🔗 Contains pharmacy-link: {'pharmacy-link' in html_content}")
            print(f"   📱 Contains phone links: {'tel:' in html_content}")
            print(f"   🗺️ Contains map links: {'maps.google.com' in html_content}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Ruta original de chat por mensaje
    print("\n3. Test ruta original /api/chat/message:")
    try:
        # Primero crear sesión
        session_response = requests.post(f"{base_url}/api/chat/session")
        if session_response.status_code == 200:
            session_data = session_response.json()
            session_id = session_data.get('session_id')
            print(f"   ✅ Session created: {session_id}")
            
            # Ahora enviar mensaje
            message_response = requests.post(
                f"{base_url}/api/chat/message",
                json={
                    "message": "emergencia maipu direcciones",
                    "session_id": session_id
                }
            )
            
            if message_response.status_code == 200:
                data = message_response.json()
                message = data.get('response', '')
                print(f"   ✅ Message response: {message_response.status_code}")
                print(f"   📝 Response length: {len(message)}")
                print(f"   🔗 Contains markdown: {'[' in message and '](' in message}")
                print(f"   📄 Preview: {message[:150]}...")
            else:
                print(f"   ❌ Message error: {message_response.status_code}")
                
        else:
            print(f"   ❌ Session error: {session_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_direct_links():
    """Test directo de los endpoints"""
    print(f"\n🔍 TEST ENLACES DIRECTOS")
    print("=" * 50)
    
    print("📋 URLs para probar manualmente:")
    print("   1. Página de test: http://127.0.0.1:8003/test-links")
    print("   2. Aplicación principal: http://127.0.0.1:8003/modern")
    print("   3. API simple: POST a http://127.0.0.1:8003/api/chat")
    print()
    print("🔧 Pasos para debuggear:")
    print("   1. Abrir http://127.0.0.1:8003/test-links")
    print("   2. Verificar que los enlaces directos funcionan")
    print("   3. Abrir consola del navegador (F12)")
    print("   4. Copiar y pegar el código JavaScript del textarea")
    print("   5. Verificar si el formatAIResponse convierte los enlaces")

if __name__ == "__main__":
    print("🔧 TEST CORREGIDO - ENLACES CLICKEABLES")
    print("=" * 60)
    
    test_corrected_api()
    test_direct_links()
    
    print(f"\n" + "="*60)
    print("🎯 CONCLUSIONES:")
    print("   • Si /test-links funciona → CSS/HTML está bien")
    print("   • Si API devuelve markdown → Backend está bien") 
    print("   • Si JavaScript no convierte → Problema en formatAIResponse")
    print("   • Si chat no usa formatAIResponse → Problema en integración")
    print()
    print("⚡ Próximo paso: Abrir /test-links y debuggear en navegador")
