#!/usr/bin/env python3
"""
Test LLM Enhanced Commune Matching for La Florida Issue
Comprehensive test to validate the new LLM + embeddings approach
"""
import sys
import os
# Add parent directory to path so we can import from the main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_enhanced_commune_matcher import LLMEnhancedCommuneMatcher, MatchResult

def test_la_florida_queries():
    """Test various La Florida query formats"""
    print("🧪 TESTING LA FLORIDA QUERIES WITH LLM ENHANCEMENT")
    print("=" * 60)
    
    matcher = LLMEnhancedCommuneMatcher()
    
    # Test queries that previously failed
    test_cases = [
        {
            "query": "farmacias en la florida",
            "expected": "La Florida",
            "description": "Original failing query"
        },
        {
            "query": "La Florida",
            "expected": "La Florida", 
            "description": "Direct commune name"
        },
        {
            "query": "buscar farmacias la florida",
            "expected": "La Florida",
            "description": "Search intent with location"
        },
        {
            "query": "necesito medicamentos en la florida",
            "expected": "La Florida",
            "description": "Need intent with location"
        },
        {
            "query": "farmacia cerca de la florida",
            "expected": "La Florida",
            "description": "Proximity intent"
        },
        {
            "query": "quiero farmacias de la florida",
            "expected": "La Florida",
            "description": "Want intent with location"
        },
        {
            "query": "hay farmacias en la florida?",
            "expected": "La Florida",
            "description": "Question format"
        },
        {
            "query": "la florida farmacias",
            "expected": "La Florida",
            "description": "Inverted order"
        },
        {
            "query": "farmacias de turno en la florida",
            "expected": "La Florida",
            "description": "Duty pharmacy query"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['description']}")
        print(f"   🔍 Query: '{test_case['query']}'")
        print(f"   🎯 Expected: '{test_case['expected']}'")
        
        result = matcher.smart_match(test_case['query'])
        
        # Check if match is correct
        is_correct = result.matched_commune == test_case['expected']
        status = "✅ PASS" if is_correct else "❌ FAIL"
        
        print(f"   {status} Got: '{result.matched_commune}' (confidence: {result.confidence:.2f})")
        print(f"   📊 Method: {result.method}")
        
        if result.location_intent:
            print(f"   🤖 LLM extracted: '{result.location_intent.extracted_location}'")
            print(f"   🤖 Intent: {result.location_intent.intent_type} ({result.location_intent.confidence:.2f})")
            print(f"   🤖 Reasoning: {result.location_intent.reasoning}")
        
        if result.suggestions and not is_correct:
            print(f"   💡 Suggestions: {result.suggestions[:3]}")
        
        results.append({
            'test': test_case,
            'result': result,
            'correct': is_correct
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['correct'])
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"✅ Passed: {passed}/{total} ({success_rate:.1f}%)")
    print(f"❌ Failed: {total - passed}/{total}")
    
    # Show failed cases
    failed_cases = [r for r in results if not r['correct']]
    if failed_cases:
        print(f"\n❌ FAILED CASES:")
        for r in failed_cases:
            print(f"   • '{r['test']['query']}' -> Got: '{r['result'].matched_commune}', Expected: '{r['test']['expected']}'")
    
    # Method analysis
    methods = {}
    for r in results:
        method = r['result'].method
        if method not in methods:
            methods[method] = {'count': 0, 'correct': 0}
        methods[method]['count'] += 1
        if r['correct']:
            methods[method]['correct'] += 1
    
    print(f"\n📊 METHOD PERFORMANCE:")
    for method, stats in methods.items():
        accuracy = (stats['correct'] / stats['count']) * 100 if stats['count'] > 0 else 0
        print(f"   • {method}: {stats['correct']}/{stats['count']} ({accuracy:.1f}%)")
    
    return results

def test_other_communes():
    """Test with other communes to ensure we didn't break anything"""
    print("\n\n🧪 TESTING OTHER COMMUNES")
    print("=" * 60)
    
    matcher = LLMEnhancedCommuneMatcher()
    
    other_tests = [
        "farmacias en las condes",
        "necesito medicamentos en Quilpué", 
        "buscar farmacias en la reina",
        "hay farmacias en villa alemana?",
        "farmacia cerca de valparaíso"
    ]
    
    for query in other_tests:
        print(f"\n🔍 Query: '{query}'")
        result = matcher.smart_match(query)
        print(f"   ✓ Matched: '{result.matched_commune}' (confidence: {result.confidence:.2f})")
        print(f"   📊 Method: {result.method}")
        if result.location_intent:
            print(f"   🤖 LLM: '{result.location_intent.extracted_location}' ({result.location_intent.confidence:.2f})")

def compare_old_vs_new():
    """Compare old regex approach vs new LLM approach"""
    print("\n\n🧪 COMPARING OLD VS NEW APPROACH")
    print("=" * 60)
    
    # Test the problematic query
    query = "farmacias en la florida"
    
    print(f"🔍 Testing: '{query}'")
    
    # New LLM approach
    llm_matcher = LLMEnhancedCommuneMatcher()
    llm_result = llm_matcher.smart_match(query)
    
    print(f"\n🆕 LLM Enhanced Approach:")
    print(f"   ✓ Matched: '{llm_result.matched_commune}'")
    print(f"   ✓ Confidence: {llm_result.confidence:.2f}")
    print(f"   ✓ Method: {llm_result.method}")
    if llm_result.location_intent:
        print(f"   🤖 LLM extracted: '{llm_result.location_intent.extracted_location}'")
    
    # Old regex approach (simulate)
    print(f"\n🔄 Old Regex Approach:")
    old_result = llm_matcher._fallback_extraction(query)
    print(f"   ✓ Extracted: '{old_result}'")
    
    if old_result:
        exact_match = llm_matcher.exact_match(old_result)
        fuzzy_matches = llm_matcher.fuzzy_match(old_result)
        print(f"   ✓ Exact match: '{exact_match}'")
        if fuzzy_matches:
            print(f"   ✓ Best fuzzy: '{fuzzy_matches[0][0]}' ({fuzzy_matches[0][1]:.2f})")

if __name__ == "__main__":
    # Run all tests
    test_la_florida_queries()
    test_other_communes()
    compare_old_vs_new()
    
    print("\n" + "🎯" * 20)
    print("TEST COMPLETE - Check results above!")
    print("🎯" * 20)
