#!/usr/bin/env python3
"""
🧪 TEST RÁPIDO - Verificar que todo esté funcionando
"""

import sys
print('🐍 Python Version:', sys.version.split()[0])

# Test imports
test_results = []

try:
    from app.main import app
    test_results.append('✅ FastAPI app import: OK')
except Exception as e:
    test_results.append(f'❌ FastAPI app import: {e}')

try:
    from app.agents.spanish_agent import SpanishPharmacyAgent
    test_results.append('✅ Spanish Agent import: OK')
except Exception as e:
    test_results.append(f'❌ Spanish Agent import: {e}')

try:
    from app.core.enhanced_pharmacy_search import EnhancedPharmacyDatabase
    test_results.append('✅ Enhanced DB import: OK')
except Exception as e:
    test_results.append(f'❌ Enhanced DB import: {e}')

try:
    import sentence_transformers
    test_results.append('✅ SentenceTransformers: OK')
except Exception as e:
    test_results.append(f'❌ SentenceTransformers: {e}')

try:
    import redis
    test_results.append('✅ Redis library: OK')
except Exception as e:
    test_results.append(f'❌ Redis library: {e}')

try:
    import openai
    test_results.append('✅ OpenAI library: OK')
except Exception as e:
    test_results.append(f'❌ OpenAI library: {e}')

print('\n📋 RESULTADOS DEL TEST:')
print('=' * 40)
for result in test_results:
    print(result)

# Verificar archivos críticos
print('\n📁 VERIFICACIÓN DE ARCHIVOS:')
print('=' * 40)
import os
critical_files = [
    'app/main.py',
    'app/agents/spanish_agent.py', 
    'app/core/enhanced_pharmacy_search.py',
    'app/core/llm_enhanced_commune_matcher.py',
    '.env.example'
]

for file in critical_files:
    if os.path.exists(file):
        print(f'✅ {file}: Existe')
    else:
        print(f'❌ {file}: No encontrado')

print('\n🎯 ESTADO GENERAL:')
print('=' * 40)
errors = [r for r in test_results if r.startswith('❌')]
if not errors:
    print('🚀 ¡TODO LISTO PARA EJECUTAR!')
    print('👉 Ejecutar: python -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload')
    print('👉 Abrir: http://localhost:8003')
else:
    print(f'⚠️  Hay {len(errors)} errores que resolver')
    for error in errors:
        print(f'   {error}')
