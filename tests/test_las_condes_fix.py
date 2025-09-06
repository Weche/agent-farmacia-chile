#!/usr/bin/env python3
"""
Test rápido para verificar el fix de Las Condes
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_las_condes_fix():
    print("🧪 TESTING LAS CONDES FIX")
    print("=" * 50)
    
    try:
        from app.agents.spanish_agent import SpanishPharmacyAgent
        
        agent = SpanishPharmacyAgent()
        session_id = await agent.create_session()
        
        # Test the exact query that was failing
        response = await agent.process_message(session_id, "dame una lista de farmacias en las condes")
        
        print(f"✅ Agent response:")
        print(f"   Tools used: {response.get('tools_used', [])}")
        print(f"   Success: {response.get('success', False)}")
        
        # Check if it used the correct tool
        if 'search_farmacias' in response.get('tools_used', []):
            print("✅ SUCCESS: Agent used search_farmacias (correct tool)")
        elif 'get_communes' in response.get('tools_used', []):
            print("❌ FAIL: Agent still using get_communes (wrong tool)")
        else:
            print("❓ UNKNOWN: Agent used different tools")
            
        print(f"   Response preview: {response.get('response', '')[:200]}...")
        
        # Test another problematic query
        print(f"\n🧪 Testing another query...")
        response2 = await agent.process_message(session_id, "¿hay farmacias en providencia?")
        
        print(f"   Tools used: {response2.get('tools_used', [])}")
        if 'search_farmacias' in response2.get('tools_used', []):
            print("✅ SUCCESS: Also works for Providencia")
        else:
            print("❌ FAIL: Still problematic")
        
        # Write results
        with open("las_condes_fix_test.txt", "w", encoding="utf-8") as f:
            f.write("LAS CONDES FIX TEST\n")
            f.write("=" * 30 + "\n\n")
            f.write(f"Query 1: 'dame una lista de farmacias en las condes'\n")
            f.write(f"Tools used: {response.get('tools_used', [])}\n")
            f.write(f"Success: {response.get('success', False)}\n")
            f.write(f"Used correct tool: {'search_farmacias' in response.get('tools_used', [])}\n\n")
            
            f.write(f"Query 2: '¿hay farmacias en providencia?'\n")
            f.write(f"Tools used: {response2.get('tools_used', [])}\n")
            f.write(f"Used correct tool: {'search_farmacias' in response2.get('tools_used', [])}\n\n")
            
            if ('search_farmacias' in response.get('tools_used', []) and 
                'search_farmacias' in response2.get('tools_used', [])):
                f.write("✅ FIX SUCCESSFUL: Agent now uses search_farmacias correctly\n")
            else:
                f.write("❌ FIX FAILED: Agent still confused about tool selection\n")
        
        print("💾 Results saved to: las_condes_fix_test.txt")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_las_condes_fix())
