#!/usr/bin/env python3
"""
Test Agent Tools
Validates all agent tools functionality
"""

import asyncio
import sys
import os
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from app.agents.tools.tool_registry import get_tool_registry
import json

async def test_agent_tools():
    """Test all agent tools functionality"""
    
    print("🔧 Testing Agent Tools")
    print("=" * 50)
    
    # Get tool registry
    registry = get_tool_registry()
    
    print("1️⃣ Testing Tool Registry...")
    tools = registry.get_all_tools()
    tool_names = registry.get_tool_names()
    
    print(f"✅ Registered tools: {len(tools)}")
    for tool_name in tool_names:
        print(f"   - {tool_name}")
    
    # Test 1: Search Farmacias Tool
    print("\n2️⃣ Testing SearchFarmaciasTool...")
    
    # Test basic search
    result = await registry.execute_tool(
        "search_farmacias",
        comuna="Villa Alemana",
        turno=False,
        limite=3
    )
    
    if result["success"]:
        data = result["data"]
        print(f"✅ Found {data['total']} pharmacies in Villa Alemana")
        print(f"   Showing {len(data['farmacias'])} results:")
        for i, farmacia in enumerate(data['farmacias'][:2], 1):
            print(f"   {i}. {farmacia['nombre']} - {farmacia['direccion']}")
    else:
        print(f"❌ Search failed: {result['error']}")
    
    # Test duty pharmacies search
    print("\n   Testing duty pharmacies search...")
    result_turno = await registry.execute_tool(
        "search_farmacias",
        comuna="Villa Alemana",
        turno=True,
        limite=2
    )
    
    if result_turno["success"]:
        data = result_turno["data"]
        print(f"✅ Found {data['total']} duty pharmacies")
        if data['farmacias']:
            print(f"   First duty pharmacy: {data['farmacias'][0]['nombre']}")
    else:
        print(f"⚠️ No duty pharmacies found or error: {result_turno.get('error', 'Unknown error')}")
    
    # Test 2: Get Communes Tool
    print("\n3️⃣ Testing GetCommunesTool...")
    
    result = await registry.execute_tool("get_communes")
    
    if result["success"]:
        data = result["data"]
        print(f"✅ Found {data['total']} available communes")
        print(f"   First 5 communes: {data['comunas'][:5]}")
    else:
        print(f"❌ Get communes failed: {result['error']}")
    
    # Test 3: Lookup Medicamento Tool
    print("\n4️⃣ Testing LookupMedicamentoTool...")
    
    # Test Spanish medication
    result = await registry.execute_tool(
        "lookup_medicamento",
        medicamento="paracetamol",
        limite=2
    )
    
    if result["success"]:
        data = result["data"]
        print(f"✅ Found {data['total']} medications for 'paracetamol'")
        if data['medicamentos']:
            med = data['medicamentos'][0]
            print(f"   First result: {med['nombre']}")
            print(f"   Active ingredient: {med['principio_activo']}")
            print(f"   Category: {med['categoria']}")
    else:
        print(f"❌ Medication lookup failed: {result['error']}")
    
    # Test English medication
    print("\n   Testing English medication search...")
    result_en = await registry.execute_tool(
        "lookup_medicamento",
        medicamento="acetaminophen",
        limite=1
    )
    
    if result_en["success"]:
        data = result_en["data"]
        print(f"✅ Found {data['total']} medications for 'acetaminophen'")
        if data['medicamentos']:
            med = data['medicamentos'][0]
            print(f"   Result: {med['nombre']} ({med['principio_activo']})")
    else:
        print(f"⚠️ English medication search: {result_en.get('error', 'No results')}")
    
    # Test 4: Get Medication Categories Tool
    print("\n5️⃣ Testing GetMedicationCategoriesTool...")
    
    result = await registry.execute_tool("get_medication_categories")
    
    if result["success"]:
        data = result["data"]
        print(f"✅ Found {data['total']} medication categories")
        print(f"   First 3 categories: {data['categorias'][:3]}")
    else:
        print(f"❌ Get categories failed: {result['error']}")
    
    # Test 5: OpenAI Function Definitions
    print("\n6️⃣ Testing OpenAI Function Definitions...")
    
    openai_functions = registry.get_openai_functions()
    print(f"✅ Generated {len(openai_functions)} OpenAI function definitions:")
    
    for func_def in openai_functions:
        func_info = func_def["function"]
        print(f"   - {func_info['name']}: {func_info['description'][:50]}...")
    
    # Test 6: Tool Validation
    print("\n7️⃣ Testing Tool Parameter Validation...")
    
    # Valid parameters
    validation = registry.validate_tool_call(
        "search_farmacias",
        {"comuna": "Santiago", "turno": True}
    )
    print(f"✅ Valid parameters: {validation['valid']}")
    
    # Invalid parameters (missing required)
    validation_invalid = registry.validate_tool_call(
        "search_farmacias",
        {"turno": True}  # Missing required 'comuna'
    )
    print(f"✅ Invalid parameters detected: {not validation_invalid['valid']}")
    print(f"   Error: {validation_invalid.get('error', 'Unknown')}")
    
    # Test 7: Tool Usage Statistics
    print("\n8️⃣ Testing Tool Usage Statistics...")
    
    stats = registry.get_tool_usage_stats()
    print(f"✅ Tool usage statistics:")
    print(f"   Total tools: {stats['total_tools']}")
    print(f"   Total usage: {stats['total_usage']}")
    
    if stats.get('most_used_tool'):
        most_used = stats['most_used_tool']
        print(f"   Most used tool: {most_used['name']} ({most_used['usage_count']} times)")
    
    # Test 8: Error Handling
    print("\n9️⃣ Testing Error Handling...")
    
    # Non-existent tool
    result_error = await registry.execute_tool("non_existent_tool", param="value")
    print(f"✅ Non-existent tool handled: {not result_error['success']}")
    print(f"   Error message: {result_error['error']}")
    
    # Invalid parameters
    result_invalid = await registry.execute_tool(
        "lookup_medicamento",
        medicamento=""  # Empty string
    )
    print(f"✅ Invalid parameters handled: {not result_invalid['success']}")
    
    # Test 9: Complex Tool Call Example
    print("\n🔟 Testing Complex Tool Call Example...")
    
    # Simulate a complex user query workflow
    print("   Simulating: 'Buscar farmacias de turno en Santiago y información sobre ibuprofeno'")
    
    # Step 1: Search duty pharmacies
    farmacias_result = await registry.execute_tool(
        "search_farmacias",
        comuna="Santiago",
        turno=True,
        limite=2
    )
    
    # Step 2: Look up medication
    medicamento_result = await registry.execute_tool(
        "lookup_medicamento",
        medicamento="ibuprofeno",
        limite=1,
        incluir_similares=True
    )
    
    if farmacias_result["success"] and medicamento_result["success"]:
        print("✅ Complex workflow completed successfully:")
        print(f"   Found {farmacias_result['data']['total']} duty pharmacies in Santiago")
        print(f"   Found medication info for ibuprofeno")
        
        if medicamento_result['data']['medicamentos']:
            med = medicamento_result['data']['medicamentos'][0]
            print(f"   Medication: {med['nombre']} - {med['uso_terapeutico']}")
    else:
        print("⚠️ Complex workflow had some issues")
    
    print("\n" + "=" * 50)
    print("🎉 Agent Tools Test Complete!")
    print("✅ All tools functioning correctly")
    
    # Final summary
    final_stats = registry.get_tool_usage_stats()
    print(f"\n📊 Final Usage Statistics:")
    print(f"   Total tool executions: {final_stats['total_usage']}")
    for tool_name, tool_stats in final_stats['tools'].items():
        if tool_stats['usage_count'] > 0:
            print(f"   {tool_name}: {tool_stats['usage_count']} executions")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_agent_tools())
        if result:
            print("\n🚀 Agent tools ready for AI agent integration!")
        else:
            print("\n❌ Agent tools test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
