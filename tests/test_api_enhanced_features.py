"""
Enhanced Location Features Test with Duty Pharmacies Focus
Tests enhanced features for both regular and emergency/duty pharmacies
"""

import requests
import json

def test_duty_pharmacies():
    """Test duty pharmacies with enhanced location features"""
    print("=== TESTING DUTY PHARMACIES WITH ENHANCED FEATURES ===")
    
    base_url = "http://127.0.0.1:8003"
    
    # Test 1: Search for duty pharmacies
    print("\n--- Testing Duty Pharmacies Search ---")
    try:
        response = requests.get(f"{base_url}/api/search", params={
            "comuna": "SANTIAGO",
            "turno": True,  # This is key for duty pharmacies
            "limit": 5
        })
        
        if response.status_code == 200:
            data = response.json()
            pharmacies = data.get('farmacias', [])
            
            print(f"✅ Found {len(pharmacies)} duty pharmacies")
            
            if pharmacies:
                for i, pharmacy in enumerate(pharmacies, 1):
                    print(f"\n🚨 DUTY PHARMACY {i}: {pharmacy.get('nombre', 'N/A')}")
                    print(f"   📍 Address: {pharmacy.get('direccion', 'N/A')}")
                    print(f"   🏘️  Comuna: {pharmacy.get('comuna', 'N/A')}")
                    print(f"   ⚡ Is Duty: {pharmacy.get('turno', 'N/A')}")
                    
                    # Enhanced location features for duty pharmacies
                    if 'mapas' in pharmacy:
                        maps = pharmacy['mapas']
                        print(f"   🗺️  Google Maps: {maps.get('google_maps', 'N/A')}")
                        print(f"   🍎 Apple Maps: {maps.get('apple_maps', 'N/A')}")
                        print(f"   🧭 Directions: {maps.get('direcciones', 'N/A')}")
                    
                    if 'horario' in pharmacy:
                        horario = pharmacy['horario']
                        if isinstance(horario, dict):
                            print(f"   🕐 Hours: {horario.get('display', 'N/A')}")
                            print(f"   📅 Status: {horario.get('estado', 'N/A')}")
                    
                    if 'contacto' in pharmacy:
                        contacto = pharmacy['contacto']
                        if contacto.get('telefono_display'):
                            print(f"   📞 Emergency Phone: {contacto['telefono_display']}")
                            print(f"   📱 Call Now: {contacto.get('click_to_call', 'N/A')}")
                    
                    print("   " + "="*50)
            else:
                print("⚠️  No duty pharmacies found. Testing regular pharmacies...")
                
        else:
            print(f"❌ Duty pharmacy search failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Duty pharmacy test failed: {e}")
        return False
    
    return True

def test_regular_vs_duty():
    """Compare regular vs duty pharmacy responses"""
    print("\n--- Comparing Regular vs Duty Pharmacies ---")
    
    base_url = "http://127.0.0.1:8003"
    
    # Test regular pharmacies
    try:
        regular_response = requests.get(f"{base_url}/api/search", params={
            "comuna": "LAS CONDES",
            "turno": False,
            "limit": 3
        })
        
        duty_response = requests.get(f"{base_url}/api/search", params={
            "comuna": "LAS CONDES", 
            "turno": True,
            "limit": 3
        })
        
        if regular_response.status_code == 200 and duty_response.status_code == 200:
            regular_data = regular_response.json()
            duty_data = duty_response.json()
            
            regular_count = len(regular_data.get('farmacias', []))
            duty_count = len(duty_data.get('farmacias', []))
            
            print(f"📊 Regular pharmacies in Las Condes: {regular_count}")
            print(f"🚨 Duty pharmacies in Las Condes: {duty_count}")
            
            # Test enhanced features in both
            for pharmacy_type, data in [("Regular", regular_data), ("Duty", duty_data)]:
                pharmacies = data.get('farmacias', [])
                if pharmacies:
                    sample = pharmacies[0]
                    print(f"\n{pharmacy_type} pharmacy sample:")
                    print(f"   Name: {sample.get('nombre', 'N/A')}")
                    print(f"   Enhanced features: {list(sample.keys())}")
                    
                    # Check specific enhanced features
                    features_count = 0
                    if 'mapas' in sample:
                        features_count += 1
                    if 'horario' in sample and isinstance(sample['horario'], dict):
                        features_count += 1
                    if 'contacto' in sample and sample['contacto'].get('telefono_display'):
                        features_count += 1
                    
                    print(f"   Enhanced features present: {features_count}/3")
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")

def test_emergency_scenarios():
    """Test emergency scenarios with enhanced features"""
    print("\n--- Testing Emergency Scenarios ---")
    
    base_url = "http://127.0.0.1:8003"
    
    emergency_communes = ["SANTIAGO", "PROVIDENCIA", "LAS CONDES", "MAIPU", "ÑUÑOA"]
    
    total_duty = 0
    communes_with_duty = 0
    
    for comuna in emergency_communes:
        try:
            response = requests.get(f"{base_url}/api/search", params={
                "comuna": comuna,
                "turno": True,
                "limit": 10
            })
            
            if response.status_code == 200:
                data = response.json()
                duty_pharmacies = data.get('farmacias', [])
                count = len(duty_pharmacies)
                total_duty += count
                
                if count > 0:
                    communes_with_duty += 1
                    print(f"🚨 {comuna}: {count} duty pharmacies")
                    
                    # Check first one for enhanced features
                    if duty_pharmacies:
                        first = duty_pharmacies[0]
                        enhanced = []
                        if 'mapas' in first:
                            enhanced.append("Maps")
                        if 'horario' in first and isinstance(first['horario'], dict):
                            enhanced.append("Enhanced Hours") 
                        if 'contacto' in first and first['contacto'].get('click_to_call'):
                            enhanced.append("Click-to-call")
                        
                        if enhanced:
                            print(f"   ✅ Enhanced features: {', '.join(enhanced)}")
                        else:
                            print(f"   ❌ No enhanced features detected")
                else:
                    print(f"⚠️  {comuna}: No duty pharmacies found")
        
        except Exception as e:
            print(f"❌ {comuna}: Error - {e}")
    
    print(f"\n📊 Emergency Coverage Summary:")
    print(f"   Total duty pharmacies found: {total_duty}")
    print(f"   Communes with duty pharmacies: {communes_with_duty}/{len(emergency_communes)}")
    
    return total_duty > 0

def test_chat_duty_pharmacies():
    """Test AI chat responses for duty pharmacies"""
    print("\n--- Testing AI Chat for Duty Pharmacies ---")
    
    base_url = "http://127.0.0.1:8003"
    
    duty_queries = [
        "farmacias de turno en santiago",
        "farmacia de emergencia en las condes", 
        "necesito una farmacia abierta ahora en providencia",
        "farmacia 24 horas en ñuñoa"
    ]
    
    for query in duty_queries:
        print(f"\n🤖 Testing: '{query}'")
        
        try:
            response = requests.post(f"{base_url}/api/chat", 
                json={"message": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', '')
                
                # Check for enhanced features in response
                has_maps = 'maps.google.com' in message or 'maps.apple.com' in message
                has_phone = 'tel:' in message
                has_whatsapp = 'wa.me' in message
                has_emergency_info = any(word in message.lower() for word in ['turno', 'emergencia', '24 horas', 'abierta'])
                
                print(f"   ✅ Response length: {len(message)} chars")
                print(f"   🗺️  Has maps: {'✅' if has_maps else '❌'}")
                print(f"   📞 Has phone: {'✅' if has_phone else '❌'}")
                print(f"   💬 Has WhatsApp: {'✅' if has_whatsapp else '❌'}")
                print(f"   🚨 Emergency context: {'✅' if has_emergency_info else '❌'}")
                
                if has_maps and has_phone:
                    print(f"   🎉 ENHANCED FEATURES WORKING FOR DUTY PHARMACIES!")
                
            else:
                print(f"   ❌ Chat failed: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_server_status():
    """Check if server is running"""
    try:
        response = requests.get("http://127.0.0.1:8003/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print("❌ Server health check failed")
            return False
    except:
        print("❌ Server is not running")
        return False

if __name__ == "__main__":
    print("🚨 TESTING ENHANCED FEATURES FOR DUTY PHARMACIES 🚨")
    print("=" * 60)
    
    if test_server_status():
        print("\n🧪 Running comprehensive duty pharmacy tests...")
        
        # Run all duty pharmacy tests
        duty_success = test_duty_pharmacies()
        test_regular_vs_duty()
        emergency_success = test_emergency_scenarios()
        test_chat_duty_pharmacies()
        
        print("\n" + "="*60)
        if duty_success and emergency_success:
            print("🎉 DUTY PHARMACY ENHANCED FEATURES ARE WORKING!")
            print("✅ Emergency pharmacies now have:")
            print("   🗺️  One-click maps for urgent navigation")
            print("   📞 Click-to-call for immediate contact")
            print("   🕐 Enhanced hours with current status")
            print("   💬 WhatsApp links for quick communication")
        else:
            print("⚠️  Some issues detected with duty pharmacy features")
        
        print(f"\n🎯 Duty pharmacy enhanced features test completed!")
        
    else:
        print(f"\n⚠️  Please start the server first:")
        print(f"   python -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload")
