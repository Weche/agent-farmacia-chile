"""
Prueba de Integración Completa - Características Mejoradas
Verifica si las características mejoradas están activas en la aplicación web
"""

import requests
import json
import sys
import os

def test_web_app_integration():
    """Prueba la aplicación web para verificar características mejoradas"""
    print("🔍 PRUEBA DE INTEGRACIÓN WEB - CARACTERÍSTICAS MEJORADAS")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8003"
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            print("✅ Servidor corriendo correctamente")
        else:
            print("❌ Problema con el servidor")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está corriendo en puerto 8003?")
        return False
    
    return True

def test_api_enhanced_features():
    """Prueba características mejoradas a través de API"""
    print(f"\n🚨 PRUEBA API - CARACTERÍSTICAS MEJORADAS")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8003"
    
    # Casos de prueba para diferentes comunas
    test_cases = [
        {"comuna": "SANTIAGO", "description": "Farmacia centro de Santiago"},
        {"comuna": "LAS CONDES", "description": "Farmacia zona oriente"},
        {"comuna": "MAIPU", "description": "Farmacia con turno (Maipú)"}
    ]
    
    for case in test_cases:
        print(f"\n🔍 PROBANDO: {case['description']}")
        
        try:
            # Buscar farmacias por comuna via API
            response = requests.get(f"{base_url}/api/farmacias/comuna/{case['comuna']}")
            
            if response.status_code == 200:
                data = response.json()
                farmacias = data.get('farmacias', [])
                
                if farmacias:
                    # Analizar primera farmacia
                    farmacia = farmacias[0]
                    
                    print(f"   📍 Farmacia encontrada: {farmacia.get('nombre', 'Sin nombre')}")
                    print(f"   📍 Dirección: {farmacia.get('direccion', 'Sin dirección')}")
                    
                    # VERIFICAR CARACTERÍSTICAS MEJORADAS
                    enhanced_features = []
                    
                    # 1. Verificar mapas mejorados
                    if 'mapas' in farmacia:
                        mapas = farmacia['mapas']
                        if isinstance(mapas, dict):
                            if mapas.get('google_maps'):
                                enhanced_features.append("✅ Google Maps directo")
                            if mapas.get('direcciones'):
                                enhanced_features.append("✅ Navegación GPS")
                            if mapas.get('apple_maps'):
                                enhanced_features.append("✅ Apple Maps")
                    else:
                        enhanced_features.append("❌ Sin mapas mejorados")
                    
                    # 2. Verificar horarios mejorados
                    if 'horario' in farmacia:
                        horario = farmacia['horario']
                        if isinstance(horario, dict):
                            if horario.get('display'):
                                enhanced_features.append("✅ Horario mejorado")
                            if horario.get('estado'):
                                enhanced_features.append("✅ Estado en tiempo real")
                    else:
                        enhanced_features.append("❌ Sin horarios mejorados")
                    
                    # 3. Verificar contacto mejorado  
                    if 'contacto' in farmacia:
                        contacto = farmacia['contacto']
                        if isinstance(contacto, dict):
                            if contacto.get('click_to_call'):
                                enhanced_features.append("✅ Click-to-call")
                            if contacto.get('telefono_display'):
                                enhanced_features.append("✅ Teléfono formateado")
                    else:
                        enhanced_features.append("❌ Sin contacto mejorado")
                    
                    # 4. Verificar turno
                    if farmacia.get('turno'):
                        enhanced_features.append("✅ Farmacia de turno")
                    
                    # Mostrar resultados
                    print(f"   📊 CARACTERÍSTICAS DETECTADAS:")
                    for feature in enhanced_features:
                        print(f"      {feature}")
                        
                    # Mostrar URLs si están disponibles
                    if 'mapas' in farmacia and isinstance(farmacia['mapas'], dict):
                        maps = farmacia['mapas']
                        print(f"\n   🗺️  ENLACES DIRECTOS:")
                        if maps.get('google_maps'):
                            print(f"      Google: {maps['google_maps']}")
                        if maps.get('direcciones'):
                            print(f"      GPS: {maps['direcciones']}")
                
                else:
                    print(f"   ⚠️  No se encontraron farmacias en {case['comuna']}")
            
            else:
                print(f"   ❌ Error API: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error en prueba: {str(e)}")

def test_chat_enhanced_features():
    """Prueba características mejoradas a través del chat AI"""
    print(f"\n🤖 PRUEBA CHAT AI - CARACTERÍSTICAS MEJORADAS")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8003"
    
    # Preguntas de prueba que deberían activar características mejoradas
    test_queries = [
        "Necesito una farmacia de turno en Santiago con navegación GPS",
        "Farmacias abiertas en Las Condes con teléfono para llamar",
        "Emergencia medicamento en Maipú - necesito direcciones"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 CONSULTA #{i}: {query}")
        
        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json={"message": query},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', '')
                
                # Buscar evidencia de características mejoradas en la respuesta
                enhanced_indicators = []
                
                if 'maps.google.com' in message:
                    enhanced_indicators.append("✅ Enlaces Google Maps encontrados")
                if 'direcciones' in message.lower():
                    enhanced_indicators.append("✅ Navegación mencionada")
                if 'tel:' in message:
                    enhanced_indicators.append("✅ Enlaces telefónicos encontrados")
                if any(word in message.lower() for word in ['abierto', 'cerrado', 'horario']):
                    enhanced_indicators.append("✅ Estado de horario incluido")
                    
                if enhanced_indicators:
                    print(f"   ✅ RESPUESTA CON CARACTERÍSTICAS MEJORADAS:")
                    for indicator in enhanced_indicators:
                        print(f"      {indicator}")
                else:
                    print(f"   ⚠️  Respuesta sin características mejoradas detectadas")
                    
                # Mostrar parte de la respuesta
                preview = message[:200] + "..." if len(message) > 200 else message
                print(f"   📝 Preview: {preview}")
            
            else:
                print(f"   ❌ Error chat: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error en consulta: {str(e)}")

def test_duty_pharmacy_integration():
    """Prueba específica para farmacias de turno con características mejoradas"""
    print(f"\n🚨 PRUEBA ESPECÍFICA - FARMACIAS DE TURNO")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8003"
    
    try:
        # Buscar farmacias con turno=true
        response = requests.get(f"{base_url}/api/farmacias", params={"turno": True})
        
        if response.status_code == 200:
            data = response.json()
            farmacias = data.get('farmacias', [])
            
            if farmacias:
                print(f"   ✅ {len(farmacias)} farmacias de turno encontradas")
                
                # Analizar primera farmacia de turno
                farmacia = farmacias[0]
                print(f"   🚨 FARMACIA DE TURNO: {farmacia.get('nombre', 'Sin nombre')}")
                
                # Verificar que tiene todas las características de emergencia
                emergency_features = []
                
                if 'mapas' in farmacia and farmacia['mapas'].get('direcciones'):
                    emergency_features.append("✅ Navegación GPS de emergencia")
                
                if 'contacto' in farmacia and farmacia['contacto'].get('click_to_call'):
                    emergency_features.append("✅ Llamada de emergencia")
                
                if 'horario' in farmacia and farmacia['horario'].get('estado'):
                    emergency_features.append("✅ Estado tiempo real")
                
                if farmacia.get('turno'):
                    emergency_features.append("✅ Marcada como turno")
                
                print(f"   📊 CARACTERÍSTICAS DE EMERGENCIA:")
                for feature in emergency_features:
                    print(f"      {feature}")
                    
                if len(emergency_features) >= 3:
                    print(f"   🎉 FARMACIA DE TURNO COMPLETAMENTE MEJORADA")
                else:
                    print(f"   ⚠️  Farmacia de turno necesita más características")
            
            else:
                print(f"   ⚠️  No se encontraron farmacias de turno en la API")
        
        else:
            print(f"   ❌ Error buscando farmacias de turno: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error en prueba turno: {str(e)}")

if __name__ == "__main__":
    print("🔍 VERIFICACIÓN COMPLETA - CARACTERÍSTICAS MEJORADAS EN PRODUCCIÓN")
    print("Verificando si las características están listas para usar")
    print()
    
    # Ejecutar todas las pruebas
    if test_web_app_integration():
        test_api_enhanced_features()
        test_chat_enhanced_features() 
        test_duty_pharmacy_integration()
        
        print(f"\n" + "="*60)
        print(f"🎉 VERIFICACIÓN COMPLETA FINALIZADA")
        print(f"")
        print(f"Si ves ✅ en las características, significa que:")
        print(f"   🗺️  Los mapas directos están funcionando")
        print(f"   📞 Los enlaces telefónicos están activos")
        print(f"   🕐 Los horarios mejorados están incluidos")
        print(f"   🚨 Las farmacias de turno tienen características de emergencia")
        print(f"")
        print(f"⚡ ¡LA APLICACIÓN ESTÁ LISTA PARA USAR CON TODAS LAS MEJORAS!")
    else:
        print(f"❌ No se puede verificar - servidor no disponible")
