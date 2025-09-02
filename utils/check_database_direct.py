#!/usr/bin/env python3
"""
Verificación de base de datos - Villa Alemana
"""

import sqlite3
import math
from datetime import datetime

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth"""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def check_database():
    print("🔍 Verificando base de datos...")
    
    # Coordenadas del usuario
    user_lat = -33.0381
    user_lng = -71.3852
    
    conn = sqlite3.connect('pharmacy_finder.db')
    cursor = conn.cursor()
    
    # 1. Verificar total de farmacias
    cursor.execute("SELECT COUNT(*) FROM pharmacies")
    total = cursor.fetchone()[0]
    print(f"📊 Total farmacias en DB: {total}")
    
    # 2. Verificar farmacias en Villa Alemana
    cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE UPPER(comuna) = 'VILLA ALEMANA'")
    villa_alemana_count = cursor.fetchone()[0]
    print(f"🏘️ Farmacias en Villa Alemana: {villa_alemana_count}")
    
    # 3. Buscar farmacias cercanas (sin filtro de horario)
    cursor.execute("""
        SELECT nombre, direccion, comuna, lat, lng, 
               hora_apertura, hora_cierre, es_turno
        FROM pharmacies 
        WHERE lat IS NOT NULL AND lng IS NOT NULL
    """)
    
    nearby_pharmacies = []
    for row in cursor.fetchall():
        nombre, direccion, comuna, lat, lng, apertura, cierre, es_turno = row
        if lat and lng:
            distance = haversine_distance(user_lat, user_lng, lat, lng)
            if distance <= 10:  # 10km radius
                nearby_pharmacies.append({
                    'nombre': nombre,
                    'direccion': direccion,
                    'comuna': comuna,
                    'distance': distance,
                    'apertura': apertura,
                    'cierre': cierre,
                    'es_turno': es_turno
                })
    
    # Ordenar por distancia
    nearby_pharmacies.sort(key=lambda x: x['distance'])
    
    print(f"\n🎯 Farmacias dentro de 10km de {user_lat}, {user_lng}:")
    print(f"📍 Encontradas: {len(nearby_pharmacies)}")
    
    for i, farmacia in enumerate(nearby_pharmacies[:10], 1):
        print(f"\n{i}. {farmacia['nombre']}")
        print(f"   📍 {farmacia['direccion']}, {farmacia['comuna']}")
        print(f"   📏 Distancia: {farmacia['distance']:.2f} km")
        print(f"   🕐 Horario: {farmacia['apertura']} - {farmacia['cierre']}")
        print(f"   🌙 Turno: {'Sí' if farmacia['es_turno'] else 'No'}")
    
    # 4. Verificar hora actual y farmacias abiertas
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    print(f"\n🕐 Hora actual: {current_time}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
