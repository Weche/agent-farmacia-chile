#!/usr/bin/env python3
"""
Buscar Viadil específicamente en el vademécum
"""

import sys
import os
sys.path.append('.')

from app.services.vademecum_service import load_vademecum, search_vademecum

def search_viadil_specifically():
    print("🔍 Buscando Viadil en el vademécum...")
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
    
    # Buscar Viadil específicamente
    print(f"\n🎯 Búsqueda exacta: 'Viadil'")
    viadil_results = search_vademecum(items, "Viadil", limit=10)
    
    if viadil_results:
        print(f"✅ Encontrados {len(viadil_results)} resultados para 'Viadil':")
        for i, result in enumerate(viadil_results, 1):
            print(f"\n{i}. 📋 {result['nombre']}")
            print(f"   🧬 Principio activo: {result['principio_activo']}")
            print(f"   💊 Forma: {result.get('forma', 'N/A')}")
            print(f"   🏥 Categoría: {result.get('categoria', 'N/A')}")
            print(f"   📄 Indicaciones: {result.get('indicaciones', 'N/A')[:150]}...")
            print(f"   ⚠️  Advertencias: {result.get('advertencias', 'N/A')[:100]}...")
    else:
        print("❌ No se encontró 'Viadil' exactamente")
    
    # Buscar variaciones
    variations = ["via", "dial", "dil", "viadil"]
    print(f"\n🔍 Búsquedas por variaciones:")
    
    for variation in variations:
        results = search_vademecum(items, variation, limit=5)
        print(f"\n   Búsqueda: '{variation}' - {len(results)} resultados")
        for result in results[:3]:  # Solo los primeros 3
            print(f"      - {result['nombre']} ({result['principio_activo']})")
    
    # Búsqueda más amplia por patrones
    print(f"\n🔍 Medicamentos que contengan 'dial' o 'dil':")
    all_matches = []
    for item in items:
        name = item.get('nombre', '').lower()
        if 'dial' in name or 'dil' in name:
            all_matches.append(item)
    
    print(f"   Encontrados {len(all_matches)} medicamentos:")
    for match in all_matches[:10]:  # Solo los primeros 10
        print(f"      - {match['nombre']} ({match['principio_activo']})")

if __name__ == "__main__":
    search_viadil_specifically()
