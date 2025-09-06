#!/usr/bin/env python3
"""
Test de integración para verificar que el sistema LLM enhanced funciona
"""

from enhanced_pharmacy_search import EnhancedPharmacyDatabase

def test_enhanced_search():
    print("🧪 TESTING ENHANCED PHARMACY SEARCH WITH LLM")
    print("=" * 60)
    
    search = EnhancedPharmacyDatabase()
    
    # Test queries que anteriormente fallaban
    test_queries = [
        "farmacias en la florida",
        "La Florida", 
        "buscar farmacias la florida",
        "necesito medicamentos en la florida",
        "farmacias en las condes",
        "buscar farmacias en quilpué"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        try:
            # El método correcto devuelve (pharmacies_list, match_result)
            pharmacies, match_result = search.smart_find_by_comuna(query)
            print(f"   ✅ Resultados: {len(pharmacies)} farmacias")
            print(f"   🤖 Comuna matched: {match_result.matched_commune}")
            print(f"   🎯 Confianza: {match_result.confidence:.2f}")
            print(f"   🔧 Método: {match_result.method}")
            
            if pharmacies:
                # Verificar que son objetos Pharmacy
                first_pharmacy = pharmacies[0]
                print(f"   📍 Ejemplo: {first_pharmacy.nombre} - {first_pharmacy.direccion}")
                print(f"   🏙️  Comuna: {first_pharmacy.comuna}")
            else:
                if match_result.suggestions:
                    print(f"   💡 Sugerencias: {match_result.suggestions[:3]}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_enhanced_search()
