#!/usr/bin/env python3
"""
Test para diagnosticar el problema de parsing de queries con La Florida
"""
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_commune_matcher import SmartCommuneMatcher, MatchResult
from enhanced_pharmacy_search import EnhancedPharmacyDatabase

def test_query_parsing():
    print("🔍 DIAGNÓSTICO DE PARSING DE QUERIES")
    print("=" * 60)
    
    # Test queries que deberían funcionar
    test_queries = [
        "La Florida",
        "florida", 
        "farmacias en la florida",
        "farmacias en La Florida",
        "buscar farmacias la florida",
        "quiero farmacias de la florida",
        "farmacias cerca de la florida",
        "farmacia la florida",
        "necesito farmacia en la florida"
    ]
    
    print("1️⃣ TESTING SMART COMMUNE MATCHER DIRECTAMENTE")
    print("-" * 50)
    
    try:
        matcher = SmartCommuneMatcher()
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            try:
                # Test different methods that might exist
                if hasattr(matcher, 'match_commune'):
                    result = matcher.match_commune(query)
                    print(f"   match_commune: {result}")
                
                if hasattr(matcher, 'find_best_match'):
                    result = matcher.find_best_match(query)
                    print(f"   find_best_match: {result}")
                    
                if hasattr(matcher, 'smart_match'):
                    result = matcher.smart_match(query)
                    print(f"   smart_match: {result}")
                    
                # Check what methods actually exist
                methods = [method for method in dir(matcher) if not method.startswith('_')]
                print(f"   Available methods: {methods}")
                break  # Just check the first query to see available methods
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Error creating SmartCommuneMatcher: {e}")
    
    print("\n2️⃣ TESTING ENHANCED SEARCH CON QUERIES ESPECÍFICAS")
    print("-" * 50)
    
    try:
        enhanced_db = EnhancedPharmacyDatabase()
        
        for query in test_queries:
            print(f"\n🔍 Enhanced Query: '{query}'")
            try:
                pharmacies, match_result = enhanced_db.smart_find_by_comuna(query)
                print(f"   ✓ Comuna matched: '{match_result.matched_commune}'")
                print(f"   ✓ Confidence: {match_result.confidence:.2f}")
                print(f"   ✓ Method: {match_result.method}")
                print(f"   ✓ Farmacias: {len(pharmacies)}")
                
                if len(pharmacies) == 0:
                    print(f"   ⚠️  PROBLEMA: No se encontraron farmacias!")
                    print(f"   ⚠️  Suggestions: {match_result.suggestions}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Error creating EnhancedPharmacyDatabase: {e}")
    
    print("\n3️⃣ ANÁLISIS DE EXTRACCIÓN DE COMUNA")
    print("-" * 50)
    
    # Manual analysis of what should be extracted
    print("Manual analysis of what comuna should be extracted:")
    for query in test_queries:
        potential_commune = extract_commune_manually(query)
        print(f"  '{query}' -> should extract: '{potential_commune}'")

def extract_commune_manually(query):
    """Manual extraction logic to see what we expect"""
    query_lower = query.lower()
    
    # Remove common words
    stop_words = ['farmacia', 'farmacias', 'en', 'de', 'la', 'el', 'del', 'cerca', 'buscar', 'quiero', 'necesito']
    
    words = query_lower.split()
    filtered_words = []
    
    i = 0
    while i < len(words):
        if words[i] == 'la' and i + 1 < len(words) and words[i + 1] == 'florida':
            filtered_words.append('la florida')
            i += 2
        elif words[i] not in stop_words:
            filtered_words.append(words[i])
            i += 1
        else:
            i += 1
    
    return ' '.join(filtered_words)

if __name__ == "__main__":
    test_query_parsing()
