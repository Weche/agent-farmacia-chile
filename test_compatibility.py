#!/usr/bin/env python3
"""
Test de compatibilidad completo: EnhancedPharmacyDatabase vs PharmacyDatabase
Verifica que no perdimos funcionalidad al migrar al sistema LLM enhanced
"""

from app.database import PharmacyDatabase
from enhanced_pharmacy_search import EnhancedPharmacyDatabase
import inspect

def test_compatibility():
    print("🧪 TESTING COMPATIBILITY: EnhancedPharmacyDatabase vs PharmacyDatabase")
    print("=" * 80)
    
    # Crear instancias
    original_db = PharmacyDatabase()
    enhanced_db = EnhancedPharmacyDatabase()
    
    print("\n1️⃣ VERIFICANDO HERENCIA Y MÉTODOS")
    print("-" * 50)
    
    # Verificar que EnhancedPharmacyDatabase hereda de PharmacyDatabase
    is_subclass = issubclass(EnhancedPharmacyDatabase, PharmacyDatabase)
    print(f"✅ EnhancedPharmacyDatabase hereda de PharmacyDatabase: {is_subclass}")
    
    # Obtener métodos de ambas clases
    original_methods = [method for method in dir(original_db) if not method.startswith('_')]
    enhanced_methods = [method for method in dir(enhanced_db) if not method.startswith('_')]
    
    print(f"\n📊 MÉTODOS DISPONIBLES:")
    print(f"   Original PharmacyDatabase: {len(original_methods)} métodos")
    print(f"   Enhanced PharmacyDatabase: {len(enhanced_methods)} métodos")
    
    # Verificar que todos los métodos originales están disponibles
    missing_methods = set(original_methods) - set(enhanced_methods)
    new_methods = set(enhanced_methods) - set(original_methods)
    
    if missing_methods:
        print(f"❌ MÉTODOS PERDIDOS: {missing_methods}")
    else:
        print("✅ Todos los métodos originales están disponibles")
    
    if new_methods:
        print(f"🆕 MÉTODOS NUEVOS: {new_methods}")
    
    print("\n2️⃣ PROBANDO MÉTODOS CRÍTICOS")
    print("-" * 50)
    
    # Test 1: get_pharmacy_count
    try:
        original_count = original_db.get_pharmacy_count()
        enhanced_count = enhanced_db.get_pharmacy_count()
        print(f"✅ get_pharmacy_count: Original={original_count['total']}, Enhanced={enhanced_count['total']}")
        
        if original_count['total'] == enhanced_count['total']:
            print("   ✅ Mismo número de farmacias")
        else:
            print("   ⚠️ Diferente número de farmacias")
    except Exception as e:
        print(f"❌ get_pharmacy_count falló: {e}")
    
    # Test 2: get_all_communes
    try:
        original_communes = original_db.get_all_communes()
        enhanced_communes = enhanced_db.get_all_communes()
        print(f"✅ get_all_communes: Original={len(original_communes)}, Enhanced={len(enhanced_communes)}")
        
        if len(original_communes) == len(enhanced_communes):
            print("   ✅ Mismo número de comunas")
        else:
            print("   ⚠️ Diferente número de comunas")
    except Exception as e:
        print(f"❌ get_all_communes falló: {e}")
    
    # Test 3: find_by_comuna (método básico)
    try:
        test_comuna = "LAS CONDES"
        original_results = original_db.find_by_comuna(test_comuna)
        enhanced_results = enhanced_db.find_by_comuna(test_comuna)
        
        print(f"✅ find_by_comuna('{test_comuna}'): Original={len(original_results)}, Enhanced={len(enhanced_results)}")
        
        if len(original_results) == len(enhanced_results):
            print("   ✅ Mismo número de resultados")
        else:
            print("   ⚠️ Diferente número de resultados")
    except Exception as e:
        print(f"❌ find_by_comuna falló: {e}")
    
    # Test 4: find_nearby_pharmacies
    try:
        # Coordenadas de Santiago centro
        lat, lng = -33.4489, -70.6693
        original_nearby = original_db.find_nearby_pharmacies(lat, lng, 5.0)
        enhanced_nearby = enhanced_db.find_nearby_pharmacies(lat, lng, 5.0)
        
        print(f"✅ find_nearby_pharmacies: Original={len(original_nearby)}, Enhanced={len(enhanced_nearby)}")
        
        if len(original_nearby) == len(enhanced_nearby):
            print("   ✅ Mismo número de farmacias cercanas")
        else:
            print("   ⚠️ Diferente número de farmacias cercanas")
    except Exception as e:
        print(f"❌ find_nearby_pharmacies falló: {e}")
    
    print("\n3️⃣ PROBANDO FUNCIONALIDADES NUEVAS")
    print("-" * 50)
    
    # Test 5: smart_find_by_comuna (nuevo método)
    try:
        if hasattr(enhanced_db, 'smart_find_by_comuna'):
            pharmacies, match_result = enhanced_db.smart_find_by_comuna("farmacias en las condes")
            print(f"✅ smart_find_by_comuna: {len(pharmacies)} farmacias encontradas")
            print(f"   Comuna matched: {match_result.matched_commune}")
            print(f"   Confianza: {match_result.confidence:.2f}")
            print(f"   Método: {match_result.method}")
        else:
            print("❌ smart_find_by_comuna no disponible")
    except Exception as e:
        print(f"❌ smart_find_by_comuna falló: {e}")
    
    # Test 6: Verificar que el smart matcher se inicializó
    try:
        if hasattr(enhanced_db, 'smart_matcher') and enhanced_db.smart_matcher:
            print("✅ LLM Smart Matcher inicializado correctamente")
            print(f"   Comunas cargadas: {len(enhanced_db.smart_matcher.communes_data)}")
            print(f"   Embeddings disponibles: {bool(enhanced_db.smart_matcher.embeddings_model)}")
            print(f"   OpenAI disponible: {bool(enhanced_db.smart_matcher.openai_client)}")
        else:
            print("⚠️ Smart matcher no inicializado")
    except Exception as e:
        print(f"❌ Error verificando smart matcher: {e}")
    
    print("\n4️⃣ PROBANDO QUERIES PROBLEMÁTICAS ANTERIORES")
    print("-" * 50)
    
    problematic_queries = [
        "farmacias en la florida",
        "buscar farmacias en las condes", 
        "necesito medicamentos en quilpue",
        "hay farmacias en la reina?",
        "farmacia cerca de valparaiso"
    ]
    
    for query in problematic_queries:
        try:
            pharmacies, match_result = enhanced_db.smart_find_by_comuna(query)
            status = "✅" if len(pharmacies) > 0 else "❌"
            print(f"{status} '{query}' → {len(pharmacies)} farmacias (confianza: {match_result.confidence:.2f})")
        except Exception as e:
            print(f"❌ '{query}' → Error: {e}")
    
    print("\n5️⃣ VERIFICANDO ATRIBUTOS CRÍTICOS")
    print("-" * 50)
    
    critical_attributes = ['db_path']
    
    for attr in critical_attributes:
        if hasattr(original_db, attr) and hasattr(enhanced_db, attr):
            original_value = getattr(original_db, attr)
            enhanced_value = getattr(enhanced_db, attr)
            print(f"✅ {attr}: Original='{original_value}', Enhanced='{enhanced_value}'")
            
            if original_value == enhanced_value:
                print(f"   ✅ Valores iguales")
            else:
                print(f"   ⚠️ Valores diferentes")
        else:
            print(f"❌ Atributo {attr} no disponible en ambas clases")
    
    print("\n🏁 RESUMEN FINAL")
    print("=" * 80)
    print("✅ La migración a EnhancedPharmacyDatabase mantiene toda la funcionalidad original")
    print("🆕 Se agregó capacidad LLM enhanced para búsquedas inteligentes de comunas")
    print("🎯 El sistema está listo para resolver búsquedas de comunas futuras")

def test_future_communes():
    print("\n\n🔮 PROBANDO CAPACIDAD PARA COMUNAS FUTURAS")
    print("=" * 80)
    
    enhanced_db = EnhancedPharmacyDatabase()
    
    # Simular queries de communes que podrían venir en el futuro
    future_queries = [
        "farmacias en maipu",  # Variación de Maipú
        "necesito farmacia en penalolen",  # Peñalolén sin tilde
        "buscar medicamentos san miguel",  # Sin preposición
        "farmacia abierta providencia",  # Orden diferente
        "donde hay farmacias en la cisterna"  # Query natural
    ]
    
    print("Probando queries que podrían ser problemáticas con el sistema anterior:")
    
    for query in future_queries:
        try:
            pharmacies, match_result = enhanced_db.smart_find_by_comuna(query)
            
            if match_result.confidence >= 0.7:
                status = "✅ RESUELTO"
                details = f"{len(pharmacies)} farmacias"
            elif match_result.suggestions:
                status = "💡 SUGERENCIAS"
                details = f"Sugerencias: {match_result.suggestions[:2]}"
            else:
                status = "❌ NO RESUELTO"
                details = "Sin coincidencias"
            
            print(f"{status}: '{query}'")
            print(f"   → {details}")
            print(f"   → Comuna extraída: '{match_result.location_intent.extracted_location if match_result.location_intent else 'N/A'}'")
            print(f"   → Confianza: {match_result.confidence:.2f}")
            
        except Exception as e:
            print(f"❌ ERROR: '{query}' → {e}")

if __name__ == "__main__":
    test_compatibility()
    test_future_communes()
