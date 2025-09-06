#!/usr/bin/env python3
"""
Test específico para diagnosticar problemas con La Florida
"""
import sys
import os
import sqlite3
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import PharmacyDatabase, find_nearby_pharmacies
from enhanced_pharmacy_search import EnhancedPharmacyDatabase
from smart_commune_matcher import SmartCommuneMatcher

def test_la_florida_diagnosis():
    """Test completo para diagnosticar problemas con La Florida"""
    
    print("🔍 DIAGNÓSTICO DE FARMACIAS EN LA FLORIDA")
    print("=" * 60)
    
    # 1. Verificar datos directos en la base de datos
    print("\n1️⃣ VERIFICACIÓN DIRECTA EN BASE DE DATOS")
    print("-" * 40)
    
    try:
        db = PharmacyDatabase()
        
        # Buscar exactamente "LA FLORIDA"
        exact_search = db.find_by_comuna("LA FLORIDA")
        print(f"✓ Búsqueda exacta 'LA FLORIDA': {len(exact_search)} farmacias")
        
        # Buscar variaciones
        variations = ["La Florida", "la florida", "LA FLORIDA", "FLORIDA"]
        for variation in variations:
            result = db.find_by_comuna(variation)
            print(f"✓ Búsqueda '{variation}': {len(result)} farmacias")
            
        # Buscar en la base de datos directamente
        print("\n📊 CONSULTA DIRECTA SQL:")
        conn = sqlite3.connect("pharmacy_finder.db")
        cursor = conn.cursor()
        
        # Ver todas las comunas que contienen "florida"
        cursor.execute("SELECT DISTINCT comuna FROM pharmacies WHERE LOWER(comuna) LIKE '%florida%'")
        florida_comunas = cursor.fetchall()
        print(f"✓ Comunas que contienen 'florida': {florida_comunas}")
        
        # Contar farmacias por variación
        cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE LOWER(comuna) = 'la florida'")
        count_lower = cursor.fetchone()[0]
        print(f"✓ Farmacias con comuna = 'la florida' (lowercase): {count_lower}")
        
        cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE comuna = 'LA FLORIDA'")
        count_upper = cursor.fetchone()[0]
        print(f"✓ Farmacias con comuna = 'LA FLORIDA' (uppercase): {count_upper}")
        
        # Ver algunas farmacias de ejemplo si existen
        cursor.execute("SELECT nombre, direccion, comuna FROM pharmacies WHERE LOWER(comuna) LIKE '%florida%' LIMIT 5")
        examples = cursor.fetchall()
        if examples:
            print(f"\n📍 EJEMPLOS DE FARMACIAS EN FLORIDA:")
            for name, address, comuna in examples:
                print(f"  - {name}: {address} ({comuna})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error en verificación directa: {e}")
    
    # 2. Verificar el smart commune matcher
    print("\n2️⃣ VERIFICACIÓN DEL SMART COMMUNE MATCHER")
    print("-" * 40)
    
    try:
        matcher = SmartCommuneMatcher()
        
        queries = ["La Florida", "la florida", "LA FLORIDA", "florida"]
        for query in queries:
            result = matcher.find_best_match(query)
            print(f"✓ Query '{query}': {result.matched_commune} (confianza: {result.confidence:.2f}, método: {result.method})")
            if result.suggestions:
                print(f"  Sugerencias: {', '.join(result.suggestions[:3])}")
        
    except Exception as e:
        print(f"❌ Error en smart matcher: {e}")
    
    # 3. Verificar enhanced search
    print("\n3️⃣ VERIFICACIÓN DEL ENHANCED SEARCH")
    print("-" * 40)
    
    try:
        enhanced_db = EnhancedPharmacyDatabase()
        
        queries = ["La Florida", "farmacias en la florida", "florida"]
        for query in queries:
            pharmacies, match_result = enhanced_db.smart_find_by_comuna(query)
            print(f"✓ Query '{query}':")
            print(f"  - Comuna matched: {match_result.matched_commune}")
            print(f"  - Confianza: {match_result.confidence:.2f}")
            print(f"  - Farmacias encontradas: {len(pharmacies)}")
            if pharmacies:
                print(f"  - Ejemplo: {pharmacies[0].nombre} - {pharmacies[0].direccion}")
        
    except Exception as e:
        print(f"❌ Error en enhanced search: {e}")
    
    # 4. Verificar búsqueda por coordenadas (La Florida está aprox en -33.5269, -70.5895)
    print("\n4️⃣ VERIFICACIÓN POR COORDENADAS")
    print("-" * 40)
    
    try:
        # Coordenadas aproximadas de La Florida
        lat, lng = -33.5269, -70.5895
        
        # Buscar en diferentes radios
        for radius in [2.0, 5.0, 10.0]:
            nearby = find_nearby_pharmacies(lat=lat, lng=lng, radius_km=radius)
            print(f"✓ Radio {radius}km desde La Florida: {len(nearby)} farmacias")
            
            if nearby:
                # Mostrar algunas comunas encontradas
                comunas_found = set(p.comuna for p in nearby[:10])
                print(f"  Comunas cercanas: {', '.join(list(comunas_found)[:5])}")
        
    except Exception as e:
        print(f"❌ Error en búsqueda por coordenadas: {e}")
    
    # 5. Listar todas las comunas disponibles que empiecen con "L"
    print("\n5️⃣ COMUNAS DISPONIBLES QUE EMPIEZAN CON 'L'")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect("pharmacy_finder.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT comuna FROM pharmacies WHERE comuna LIKE 'L%' ORDER BY comuna")
        l_comunas = cursor.fetchall()
        
        print("✓ Comunas disponibles que empiezan con 'L':")
        for i, (comuna,) in enumerate(l_comunas[:20], 1):  # Mostrar las primeras 20
            print(f"  {i:2d}. {comuna}")
        
        if len(l_comunas) > 20:
            print(f"  ... y {len(l_comunas) - 20} más")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error listando comunas: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 DIAGNÓSTICO COMPLETADO")
    print("\n💡 POSIBLES CAUSAS SI NO HAY RESULTADOS:")
    print("   1. La comuna se almacena con nombre diferente")
    print("   2. No hay datos de farmacias para esa comuna")
    print("   3. Problema en el matching de nombres")
    print("   4. Base de datos incompleta")

if __name__ == "__main__":
    test_la_florida_diagnosis()
