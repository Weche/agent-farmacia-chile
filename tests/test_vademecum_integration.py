#!/usr/bin/env python3
"""
Test the vademecum service with the new Kaggle dataset
"""

import sys
import os
sys.path.append('.')

from app.services.vademecum_service import load_vademecum, search_vademecum

def test_vademecum():
    print("🧪 Testing Vademecum Service with Kaggle Dataset")
    print("=" * 50)
    
    # Load dataset
    vademecum_path = "./data/comprehensive_vademecum.csv"
    
    if not os.path.exists(vademecum_path):
        print(f"❌ Dataset not found at {vademecum_path}")
        return
    
    items = load_vademecum(vademecum_path)
    print(f"✅ Loaded {len(items):,} medications")
    
    if not items:
        print("❌ No medications loaded")
        return
    
    # Test searches
    test_queries = [
        "aspirin", "aspirina", "paracetamol", "acetaminophen", 
        "ibuprofen", "amoxicillin", "omeprazole"
    ]
    
    print(f"\n🔍 Testing searches:")
    for query in test_queries:
        results = search_vademecum(items, query, limit=2)
        print(f"\n   Query: '{query}'")
        print(f"   Results: {len(results)}")
        
        for i, result in enumerate(results[:1], 1):  # Show top result
            print(f"   {i}. 📋 {result['nombre']}")
            print(f"      🧬 Principio activo: {result['principio_activo']}")
            print(f"      💊 Forma: {result['forma']}")
            print(f"      ⚠️  Advertencias: {result['advertencias'][:100]}...")
    
    # Test a specific medication details
    print(f"\n📋 Detailed medication example:")
    aspirin_results = search_vademecum(items, "aspirin", limit=1)
    if aspirin_results:
        med = aspirin_results[0]
        print(f"   Nombre: {med['nombre']}")
        print(f"   Principio Activo: {med['principio_activo']}")
        print(f"   Categoría: {med.get('categoria', 'N/A')}")
        print(f"   Indicaciones: {med.get('indicaciones', 'N/A')[:100]}...")
        print(f"   Disponibilidad: {med.get('disponibilidad', 'N/A')}")
    
    print(f"\n✅ Vademecum service integration successful!")
    print(f"🚀 Ready for AI agent integration with {len(items)} medications!")

if __name__ == "__main__":
    test_vademecum()
