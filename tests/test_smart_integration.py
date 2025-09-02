#!/usr/bin/env python3
"""
Test Smart Commune Matching Integration
Tests the enhanced pharmacy search with smart commune matching
"""
import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.agents.tools.farmacia_tools import SearchFarmaciasTool
import asyncio
import json

async def test_smart_search():
    """Test the smart search functionality"""
    print("🧪 Testing Smart Commune Matching Integration")
    print("=" * 60)
    
    # Initialize the search tool
    search_tool = SearchFarmaciasTool()
    
    # Test cases with various types of queries
    test_cases = [
        {
            "name": "Exact match (Quilpué with accent)",
            "params": {"comuna": "Quilpué", "turno": True},
            "expected": "Should find turno pharmacies in QUILPUE"
        },
        {
            "name": "Without accent (Quilpue)",
            "params": {"comuna": "Quilpue", "turno": True},
            "expected": "Should find turno pharmacies in QUILPUE"
        },
        {
            "name": "Typo (kilpue)",
            "params": {"comuna": "kilpue", "turno": True},
            "expected": "Should suggest QUILPUE or find it with high confidence"
        },
        {
            "name": "Missing letter (quilpe)",
            "params": {"comuna": "quilpe", "turno": True},
            "expected": "Should match to QUILPUE"
        },
        {
            "name": "Complex name (Viña del Mar)",
            "params": {"comuna": "vina del mar", "turno": False},
            "expected": "Should find all pharmacies in VIÑA DEL MAR"
        },
        {
            "name": "Non-existent (xyz123)",
            "params": {"comuna": "xyz123", "turno": True},
            "expected": "Should return no matches and no suggestions"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Query: {test_case['params']}")
        print(f"   Expected: {test_case['expected']}")
        
        try:
            # Execute the search
            result = await search_tool.execute(**test_case['params'])
            
            # Analyze results
            if 'error' in result and 'suggestions' in result:
                print(f"   ❌ No match found")
                print(f"   💡 Suggestions: {', '.join(result['suggestions']['alternatives'][:3])}")
                print(f"   🔍 Method: {result['suggestions']['method']}, Confidence: {result['suggestions']['confidence']:.3f}")
            
            elif 'farmacias' in result and result['farmacias']:
                count = len(result['farmacias'])
                total = result.get('total', count)
                comuna_found = result['farmacias'][0]['comuna'] if result['farmacias'] else 'Unknown'
                print(f"   ✅ Found {count} pharmacies (total: {total}) in {comuna_found}")
                
                # Show first pharmacy as example
                if result['farmacias']:
                    first = result['farmacias'][0]
                    turno_status = "🟢 TURNO" if first.get('turno') else "⚪ Regular"
                    print(f"   📍 Example: {first['nombre']} - {first['direccion']} {turno_status}")
            
            elif 'total' in result and result['total'] == 0:
                print(f"   ⚠️ No pharmacies found")
                if 'suggestions' in result:
                    print(f"   💡 Suggestions available")
            
            else:
                print(f"   ❓ Unexpected result format")
                print(f"   📄 Keys: {list(result.keys())}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Smart matching integration test completed!")

def test_tool_properties():
    """Test that the tool has correct properties"""
    print("\n🔧 Testing Tool Properties")
    print("-" * 30)
    
    search_tool = SearchFarmaciasTool()
    
    print(f"Tool name: {search_tool.name}")
    print(f"Enhanced matching: {getattr(search_tool, 'use_smart_matching', False)}")
    print(f"Description: {search_tool.description}")
    
    # Test schema
    try:
        schema = search_tool.get_parameters_schema()
        print(f"Parameters schema: {list(schema.get('properties', {}).keys())}")
    except Exception as e:
        print(f"Schema error: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting Smart Commune Matching Tests")
    test_tool_properties()
    await test_smart_search()

if __name__ == "__main__":
    asyncio.run(main())
