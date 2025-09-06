"""
Interactive Enhanced Features Test
Run this to manually test the enhanced location features
"""

import requests
import json
import webbrowser

def interactive_test():
    """Interactive test for enhanced features"""
    print("🧪 INTERACTIVE ENHANCED LOCATION FEATURES TEST")
    print("=" * 60)
    
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
    
    print("✅ Server is running\n")
    
    # Get user input
    comuna = input("Enter commune name (e.g., 'santiago', 'las condes'): ").strip()
    if not comuna:
        comuna = "santiago"
    
    print(f"\n🔍 Searching for pharmacies in: {comuna}")
    
    try:
        # Make API request
        response = requests.get(f"{base_url}/api/search", params={
            "comuna": comuna.upper(),
            "limit": 5
        })
        
        if response.status_code == 200:
            data = response.json()
            pharmacies = data.get('farmacias', [])
            
            print(f"\n✅ Found {len(pharmacies)} pharmacies")
            
            if not pharmacies:
                print("No pharmacies found. Try a different commune.")
                return
            
            # Display results with enhanced features
            for i, pharmacy in enumerate(pharmacies, 1):
                print(f"\n📍 PHARMACY {i}: {pharmacy.get('nombre', 'Unknown')}")
                print(f"   📍 Address: {pharmacy.get('direccion', 'N/A')}")
                
                # Enhanced Maps
                if 'mapas' in pharmacy:
                    maps = pharmacy['mapas']
                    google_url = maps.get('google_maps', '')
                    apple_url = maps.get('apple_maps', '')
                    
                    print(f"   🗺️  Google Maps: {google_url}")
                    print(f"   🍎 Apple Maps: {apple_url}")
                    
                    # Ask if user wants to open maps
                    if i == 1:  # Only ask for first pharmacy
                        open_maps = input(f"   🌐 Open {pharmacy['nombre']} in Google Maps? (y/n): ").lower()
                        if open_maps == 'y':
                            webbrowser.open(google_url)
                            print("   ✅ Opened in browser")
                
                # Enhanced Hours
                if 'horario' in pharmacy:
                    horario = pharmacy['horario']
                    if isinstance(horario, dict):
                        display = horario.get('display', 'N/A')
                        estado = horario.get('estado', 'N/A')
                        print(f"   🕐 Hours: {display}")
                        print(f"   📅 Status: {estado}")
                    else:
                        print(f"   🕐 Hours: {horario}")
                
                # Enhanced Contact
                if 'contacto' in pharmacy:
                    contacto = pharmacy['contacto']
                    phone_display = contacto.get('telefono_display', '')
                    click_to_call = contacto.get('click_to_call', '')
                    whatsapp = contacto.get('whatsapp', '')
                    
                    if phone_display:
                        print(f"   📞 Phone: {phone_display}")
                        if click_to_call:
                            print(f"   📱 Click-to-call: {click_to_call}")
                        if whatsapp:
                            print(f"   💬 WhatsApp: {whatsapp}")
                
                print("   " + "-" * 50)
            
            # Test chat endpoint
            print(f"\n🤖 Testing AI Chat with enhanced features...")
            chat_response = requests.post(f"{base_url}/api/chat", 
                json={"message": f"farmacias en {comuna}"},
                timeout=30
            )
            
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                message = chat_data.get('message', '')
                
                # Check for enhanced features in chat
                has_maps = 'maps.google.com' in message
                has_whatsapp = 'wa.me' in message
                has_tel = 'tel:' in message
                
                print(f"   ✅ Chat responded ({len(message)} chars)")
                print(f"   🗺️  Contains maps URLs: {'✅' if has_maps else '❌'}")
                print(f"   📞 Contains click-to-call: {'✅' if has_tel else '❌'}")
                print(f"   💬 Contains WhatsApp links: {'✅' if has_whatsapp else '❌'}")
                
                # Show sample
                if has_maps or has_tel or has_whatsapp:
                    print(f"\n🎉 ENHANCED FEATURES ARE WORKING!")
                else:
                    print(f"\n⚠️  Enhanced features not detected in chat response")
                
                print(f"\nChat preview:\n{message[:300]}...")
            
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    interactive_test()
    print(f"\n🎯 Interactive test completed!")
    input("Press Enter to exit...")
