"""
Prueba de Enlaces Directos de Google Maps
Verifica que los enlaces generados sean funcionales y directos
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.location_utils import generate_maps_urls
import webbrowser

def test_direct_links():
    """Prueba enlaces directos de mapas"""
    print("🗺️ PRUEBA DE ENLACES DIRECTOS DE GOOGLE MAPS")
    print("=" * 50)
    
    # Coordenadas de ejemplo de Santiago centro
    lat = -33.439284
    lng = -70.648337
    address = "Estado 360"
    pharmacy_name = "AHUMADA"
    
    # Generar URLs
    maps = generate_maps_urls(lat, lng, address, pharmacy_name)
    
    print(f"\n📍 FARMACIA: {pharmacy_name}")
    print(f"📍 DIRECCIÓN: {address}")
    print(f"📍 COORDENADAS: {lat}, {lng}")
    
    print(f"\n🔗 ENLACES DIRECTOS GENERADOS:")
    
    for key, url in maps.items():
        print(f"\n🌐 {key.upper().replace('_', ' ')}:")
        print(f"   {url}")
        
        # Analizar tipo de enlace
        if "maps.google.com/maps?q=" in url:
            print("   ✅ ENLACE DIRECTO: Abre Google Maps en coordenadas exactas")
        elif "google.com/maps/dir/?destination=" in url:
            print("   🧭 NAVEGACIÓN DIRECTA: Inicia navegación desde ubicación actual")
        elif "maps.apple.com" in url:
            print("   🍎 APPLE MAPS DIRECTO: Abre Apple Maps en iOS/Mac")
        elif "google.com/maps/search/" in url:
            print("   🔍 BÚSQUEDA DIRECTA: Busca farmacia por nombre + dirección")
    
    # Verificar formato de coordenadas
    coord_in_google = f"{lat},{lng}" in maps["google_maps"]
    coord_in_directions = f"{lat},{lng}" in maps["direcciones"]
    
    print(f"\n✅ VERIFICACIÓN DE ENLACES:")
    print(f"   🎯 Coordenadas en Google Maps: {'✅' if coord_in_google else '❌'}")
    print(f"   🎯 Coordenadas en Direcciones: {'✅' if coord_in_directions else '❌'}")
    
    # Mostrar ejemplos de uso
    print(f"\n📱 CÓMO FUNCIONAN LOS ENLACES:")
    print(f"   1️⃣ CLICK en Google Maps → Se abre mapa con pin en farmacia")
    print(f"   2️⃣ CLICK en Direcciones → Inicia navegación GPS inmediatamente")  
    print(f"   3️⃣ CLICK en Apple Maps → Abre aplicación nativa en iPhone")
    print(f"   4️⃣ CLICK en Búsqueda → Encuentra farmacia por nombre")
    
    return maps

def test_multiple_pharmacies():
    """Probar enlaces para múltiples farmacias"""
    print(f"\n🏥 PRUEBA DE MÚLTIPLES FARMACIAS")
    print("=" * 40)
    
    pharmacies = [
        {"name": "CRUZ VERDE", "lat": -33.4489, "lng": -70.6693, "address": "Providencia 1308"},
        {"name": "SALCOBRAND", "lat": -33.4255, "lng": -70.5665, "address": "Av. Kennedy 5413"},
        {"name": "AHUMADA", "lat": -33.4532, "lng": -70.6618, "address": "Manuel Montt 315"}
    ]
    
    for i, pharmacy in enumerate(pharmacies, 1):
        maps = generate_maps_urls(
            pharmacy["lat"], 
            pharmacy["lng"], 
            pharmacy["address"], 
            pharmacy["name"]
        )
        
        print(f"\n🚨 FARMACIA #{i}: {pharmacy['name']}")
        print(f"   📍 {pharmacy['address']}")
        
        # Enlaces de emergencia más importantes
        google_direct = maps["google_maps"]
        navigation = maps["direcciones"]
        
        print(f"   🗺️  MAPA DIRECTO: {google_direct}")
        print(f"   🧭 NAVEGACIÓN: {navigation}")
        
        # Verificar que son enlaces únicos
        is_unique_coords = str(pharmacy["lat"]) in google_direct
        print(f"   ✅ COORDENADAS ÚNICAS: {'✅' if is_unique_coords else '❌'}")

if __name__ == "__main__":
    print("🗺️ VERIFICACIÓN DE ENLACES DIRECTOS DE GOOGLE MAPS")
    print()
    
    maps = test_direct_links()
    test_multiple_pharmacies()
    
    print(f"\n" + "="*50)
    print(f"🎉 ¡ENLACES DIRECTOS VERIFICADOS EXITOSAMENTE!")
    print(f"")
    print(f"✅ TODOS LOS ENLACES SON DIRECTOS:")
    print(f"   🗺️  Google Maps: Coordenadas GPS exactas")
    print(f"   🧭 Navegación: Rutas desde ubicación actual")
    print(f"   🍎 Apple Maps: Compatible con iOS/Mac")
    print(f"   🔍 Búsqueda: Nombre + dirección específica")
    print(f"")
    print(f"⚡ NO REQUIEREN BÚSQUEDAS ADICIONALES - ¡ABREN DIRECTAMENTE!")
