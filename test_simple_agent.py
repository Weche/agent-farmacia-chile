#!/usr/bin/env python3
"""
Test simple para entender el comportamiento del agente
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_simple_query():
    print("🧪 TESTING SIMPLE AGENT QUERY")
    print("=" * 60)
    
    # Simular consulta directa
    from app.agents.tools.farmacia_tools import SearchFarmaciasTool
    
    tool = SearchFarmaciasTool()
    
    # Test directo del tool (ahora con await y **kwargs)
    result = await tool.execute(comuna="Salamanca", turno=False)
    
    print("📋 DIRECT TOOL TEST:")
    print(f"Success: {result.get('success', False)}")
    print(f"Total farmacias: {result.get('total', 0)}")
    
    if result.get('farmacias'):
        print("✅ Farmacias encontradas:")
        for farmacia in result['farmacias'][:2]:
            print(f"   - {farmacia['nombre']}: {farmacia['direccion']}")
    
    # Now test what happens when agent says it's going to search but doesn't
    print(f"\n🔍 TESTING AGENT TOOL SELECTION ISSUE")
    print("El problema parece ser que el agente:")
    print("1. ✅ Identifica que necesita buscar farmacias en Salamanca")
    print("2. ❌ Elige get_communes en lugar de search_farmacias")
    print("3. ❌ No procede a ejecutar search_farmacias después")
    
    print(f"\n💡 POSIBLES SOLUCIONES:")
    print("1. Mejorar el system prompt para ser más específico")
    print("2. Verificar que el tool está correctamente registrado")
    print("3. Agregar ejemplos más claros en el prompt")

if __name__ == "__main__":
    asyncio.run(test_simple_query())
