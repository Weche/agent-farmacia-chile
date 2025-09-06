#!/usr/bin/env python3
"""
Test directo para diagnosticar el problema del agente con Salamanca
"""

import asyncio
from app.agents.tools.farmacia_tools import SearchFarmaciasTool

async def test_salamanca_search():
    print("🧪 TESTING SALAMANCA SEARCH DIRECTLY")
    print("=" * 60)
    
    # Crear el tool directamente
    search_tool = SearchFarmaciasTool()
    
    # Test 1: Buscar farmacias en Salamanca
    print("\n1️⃣ Buscando farmacias en Salamanca...")
    result = await search_tool.execute(comuna="Salamanca")
    
    print(f"Resultado:")
    print(f"  Total: {result.get('total', 0)}")
    print(f"  Error: {result.get('error', 'Ninguno')}")
    print(f"  Mensaje: {result.get('mensaje', 'Sin mensaje')}")
    
    if result.get('farmacias'):
        print(f"  Primeras 3 farmacias:")
        for i, farmacia in enumerate(result['farmacias'][:3]):
            print(f"    {i+1}. {farmacia['nombre']} - {farmacia['direccion']}")
    
    if result.get('suggestions'):
        print(f"  Sugerencias: {result['suggestions']}")
    
    # Test 2: Verificar si Salamanca está en la base de datos
    print("\n2️⃣ Verificando comunas disponibles...")
    from app.database import PharmacyDatabase
    db = PharmacyDatabase()
    
    all_communes = db.get_all_communes()
    salamanca_variants = [c for c in all_communes if 'salamanca' in c.lower()]
    
    print(f"Comunas con 'salamanca': {salamanca_variants}")
    print(f"Total comunas en DB: {len(all_communes)}")
    
    # Test 3: Verificar Enhanced Database
    print("\n3️⃣ Probando Enhanced Database...")
    try:
        from enhanced_pharmacy_search import EnhancedPharmacyDatabase
        enhanced_db = EnhancedPharmacyDatabase()
        
        pharmacies, match_result = enhanced_db.smart_find_by_comuna("Salamanca")
        print(f"Enhanced DB:")
        print(f"  Farmacias encontradas: {len(pharmacies)}")
        print(f"  Comuna matched: {match_result.matched_commune}")
        print(f"  Confianza: {match_result.confidence:.2f}")
        print(f"  Método: {match_result.method}")
        
        if match_result.suggestions:
            print(f"  Sugerencias: {match_result.suggestions[:3]}")
    
    except Exception as e:
        print(f"Error con Enhanced DB: {e}")
    
    # Test 4: Buscar con smart matching
    print("\n4️⃣ Probando con smart matching directo...")
    try:
        from llm_enhanced_commune_matcher import LLMEnhancedCommuneMatcher
        matcher = LLMEnhancedCommuneMatcher()
        match_result = matcher.smart_match("Salamanca")
        
        print(f"Smart Matcher:")
        print(f"  Comuna matched: {match_result.matched_commune}")
        print(f"  Confianza: {match_result.confidence:.2f}")
        print(f"  Método: {match_result.method}")
        if match_result.location_intent:
            print(f"  LLM extrajo: '{match_result.location_intent.extracted_location}'")
            print(f"  LLM confianza: {match_result.location_intent.confidence:.2f}")
        
        if match_result.suggestions:
            print(f"  Sugerencias: {match_result.suggestions[:3]}")
    
    except Exception as e:
        print(f"Error con Smart Matcher: {e}")

if __name__ == "__main__":
    asyncio.run(test_salamanca_search())
