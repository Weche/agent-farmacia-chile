"""
Interactive Duty Pharmacy Test with Enhanced Location Features
Special focus on emergency/duty pharmacies ("farmacias de turno")
"""

import requests
import json
import webbrowser
from datetime import datetime

def interactive_duty_test():
    """Interactive test specifically for duty pharmacies"""
    print("🚨 INTERACTIVE DUTY PHARMACY TEST WITH ENHANCED FEATURES")
    print("=" * 70)
    
    base_url = "http://127.0.0.1:8003"
    
    # Test server connection
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding. Please start the server first:")
            print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload")
            return
    except:
        print("❌ Server not running. Please start the server first:")
        print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload")
        return
    
    print("✅ Server is running")
    print(f"🕐 Current time: {datetime.now().strftime('%A, %H:%M:%S')}")
    print()
    
    # Get user input
    print("🚨 EMERGENCY PHARMACY SEARCH")
    comuna = input("Enter commune for emergency pharmacy search (e.g., 'santiago'): ").strip()
    if not comuna:
        comuna = "santiago"
    
    print(f"\n🔍 Searching for DUTY PHARMACIES in: {comuna}")
    print("   (These are emergency pharmacies available outside regular hours)")
    
    try:
        # Search for duty pharmacies
        duty_response = requests.get(f"{base_url}/api/search", params={
            "comuna": comuna.upper(),
            "turno": True,  # KEY: This searches for duty pharmacies
            "limit": 5
        })
        
        # Also search regular pharmacies for comparison
        regular_response = requests.get(f"{base_url}/api/search", params={
            "comuna": comuna.upper(),
            "turno": False,
            "limit": 3
        })
        
        if duty_response.status_code == 200:
            duty_data = duty_response.json()
            duty_pharmacies = duty_data.get('farmacias', [])
            
            regular_data = regular_response.json() if regular_response.status_code == 200 else {}
            regular_pharmacies = regular_data.get('farmacias', [])
            
            print(f"\n📊 SEARCH RESULTS:")
            print(f"   🚨 Duty pharmacies: {len(duty_pharmacies)}")
            print(f"   🏪 Regular pharmacies: {len(regular_pharmacies)}")
            
            if not duty_pharmacies:
                print("\n⚠️  NO DUTY PHARMACIES FOUND!")
                print("   This means no emergency pharmacies are currently available.")
                print("   Let's check regular pharmacies instead...")
                pharmacies_to_show = regular_pharmacies
                pharmacy_type = "REGULAR"
            else:
                pharmacies_to_show = duty_pharmacies
                pharmacy_type = "DUTY"
            
            if not pharmacies_to_show:
                print("❌ No pharmacies found at all. Try a different commune.")
                return
            
            # Display results with enhanced features
            print(f"\n🚨 {pharmacy_type} PHARMACIES WITH ENHANCED LOCATION FEATURES:")
            print("=" * 70)
            
            for i, pharmacy in enumerate(pharmacies_to_show, 1):
                is_duty = pharmacy.get('turno', False)
                duty_indicator = "🚨 DUTY" if is_duty else "🏪 REGULAR"
                
                print(f"\n{duty_indicator} PHARMACY {i}: {pharmacy.get('nombre', 'Unknown')}")
                print(f"   📍 Address: {pharmacy.get('direccion', 'N/A')}")
                print(f"   🏘️  Comuna: {pharmacy.get('comuna', 'N/A')}")
                
                # Enhanced Maps - Critical for emergencies
                if 'mapas' in pharmacy:
                    maps = pharmacy['mapas']
                    google_url = maps.get('google_maps', '')
                    apple_url = maps.get('apple_maps', '')
                    directions_url = maps.get('direcciones', '')
                    
                    print(f"   🗺️  Google Maps: {google_url}")
                    print(f"   🍎 Apple Maps: {apple_url}")
                    print(f"   🧭 Get Directions: {directions_url}")
                    
                    # Emergency: Ask if user wants to navigate immediately
                    if i == 1 and is_duty:
                        navigate = input(f"   🚨 EMERGENCY NAVIGATION: Open directions to {pharmacy['nombre']}? (y/n): ").lower()
                        if navigate == 'y':
                            webbrowser.open(directions_url)
                            print("   ✅ Emergency navigation opened!")
                
                # Enhanced Hours - Critical for knowing if open
                if 'horario' in pharmacy:
                    horario = pharmacy['horario']
                    if isinstance(horario, dict):
                        display = horario.get('display', 'N/A')
                        estado = horario.get('estado', 'N/A')
                        
                        status_emoji = {
                            'abierta': '✅ OPEN',
                            'cerrada': '❌ CLOSED', 
                            'por_abrir': '🕐 OPENS LATER'
                        }.get(estado.lower(), f'❓ {estado.upper()}')
                        
                        print(f"   🕐 Hours: {display}")
                        print(f"   📅 Current Status: {status_emoji}")
                        
                        if is_duty:
                            print(f"   ⚡ DUTY PHARMACY: Available for emergencies")
                    else:
                        print(f"   🕐 Hours: {horario}")
                
                # Enhanced Contact - Critical for emergencies
                if 'contacto' in pharmacy:
                    contacto = pharmacy['contacto']
                    phone_display = contacto.get('telefono_display', '')
                    click_to_call = contacto.get('click_to_call', '')
                    whatsapp = contacto.get('whatsapp', '')
                    
                    if phone_display:
                        print(f"   📞 Emergency Phone: {phone_display}")
                        if click_to_call:
                            print(f"   📱 Click-to-call: {click_to_call}")
                            if i == 1 and is_duty:
                                call_now = input(f"   📞 CALL NOW for emergency? Copy this link: {click_to_call} (Enter to continue): ")
                        if whatsapp:
                            print(f"   💬 WhatsApp: {whatsapp}")
                
                print("   " + "-" * 60)
            
            # Test AI Chat for duty pharmacy queries
            print(f"\n🤖 TESTING AI CHAT FOR EMERGENCY REQUESTS...")
            
            emergency_queries = [
                f"necesito una farmacia de turno en {comuna}",
                f"farmacia de emergencia abierta ahora en {comuna}",
                f"donde hay farmacia 24 horas en {comuna}"
            ]
            
            for query in emergency_queries:
                print(f"\n💬 Query: '{query}'")
                
                chat_response = requests.post(f"{base_url}/api/chat", 
                    json={"message": query},
                    timeout=30
                )
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    message = chat_data.get('message', '')
                    
                    # Check for enhanced features in emergency response
                    has_maps = 'maps.google.com' in message
                    has_directions = 'maps.google.com/dir' in message
                    has_phone = 'tel:' in message
                    has_whatsapp = 'wa.me' in message
                    has_emergency_keywords = any(word in message.lower() for word in 
                                                ['turno', 'emergencia', '24 horas', 'abierta', 'urgencia'])
                    
                    print(f"   ✅ AI responded ({len(message)} chars)")
                    print(f"   🗺️  Has maps: {'✅' if has_maps else '❌'}")
                    print(f"   🧭 Has directions: {'✅' if has_directions else '❌'}")
                    print(f"   📞 Has click-to-call: {'✅' if has_phone else '❌'}")
                    print(f"   💬 Has WhatsApp: {'✅' if has_whatsapp else '❌'}")
                    print(f"   🚨 Emergency context: {'✅' if has_emergency_keywords else '❌'}")
                    
                    # Show emergency-relevant sample
                    if has_emergency_keywords:
                        lines = message.split('\n')
                        emergency_lines = [line for line in lines if any(word in line.lower() for word in 
                                         ['turno', 'emergencia', 'tel:', 'maps.google', 'abierta'])]
                        if emergency_lines:
                            print(f"   🚨 Emergency info sample:")
                            for line in emergency_lines[:3]:
                                print(f"      {line.strip()}")
                
                break  # Just test first query for demo
            
        else:
            print(f"❌ Search failed: {duty_response.status_code}")
            print(f"Response: {duty_response.text}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    interactive_duty_test()
    print(f"\n🚨 Emergency pharmacy enhanced features test completed!")
    print(f"   Enhanced features provide critical information for emergencies:")
    print(f"   🗺️  Instant navigation to pharmacy")
    print(f"   📞 One-click emergency calling")
    print(f"   🕐 Real-time open/closed status")
    print(f"   💬 Multiple contact options")
    input("\nPress Enter to exit...")
