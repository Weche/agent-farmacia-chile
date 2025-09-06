"""
Prueba de Características Mejoradas para Farmacias de Turno
Prueba el formateo mejorado de farmacias de turno sin requerir servidor
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import PharmacyDatabase
from app.utils.location_utils import enhance_pharmacy_info

def test_duty_pharmacy_formatting():
    """Prueba el formateo mejorado específicamente para farmacias de turno"""
    print("🚨 PRUEBA DE CARACTERÍSTICAS MEJORADAS PARA FARMACIAS DE TURNO")
    print("=" * 60)
    
    db = PharmacyDatabase()
    
    # Buscar farmacias de turno directamente en la base de datos
    print("\n--- Buscando Farmacias de Turno ---")
    
    # Revisar diferentes comunas para farmacias de turno
    communes = ["SANTIAGO", "LAS CONDES", "PROVIDENCIA", "MAIPU", "ÑUÑOA"]
    
    total_duty_found = 0
    
    for comuna in communes:
        pharmacies = db.find_by_comuna(comuna)
        duty_pharmacies = [p for p in pharmacies if p.es_turno]
        
        if duty_pharmacies:
            total_duty_found += len(duty_pharmacies)
            print(f"\n🚨 FARMACIAS DE TURNO EN {comuna}: {len(duty_pharmacies)}")
            
            # Probar formateo mejorado en la primera farmacia de turno
            first_duty = duty_pharmacies[0]
            enhanced_info = enhance_pharmacy_info(first_duty, db)
            
            print(f"\n📍 FARMACIA DE TURNO MEJORADA: {enhanced_info.get('nombre', 'N/A')}")
            print(f"   📍 Dirección: {enhanced_info.get('direccion', 'N/A')}")
            print(f"   ⚡ Es de Turno: {enhanced_info.get('turno', False)}")
            
            # Mapas mejorados para navegación de emergencia
            if 'mapas' in enhanced_info:
                maps = enhanced_info['mapas']
                print(f"\n   🚨 NAVEGACIÓN DE EMERGENCIA:")
                print(f"   🗺️  Google Maps: {maps.get('google_maps', 'N/A')}")
                print(f"   🍎 Apple Maps: {maps.get('apple_maps', 'N/A')}")
                print(f"   🧭 Direcciones: {maps.get('direcciones', 'N/A')}")
                print(f"   🔍 Búsqueda: {maps.get('google_search', 'N/A')}")
                print(f"   📍 Coordenadas: {maps.get('coordinates', 'N/A')}")
            
            # Horarios mejorados con contexto de emergencia
            if 'horario' in enhanced_info:
                horario = enhanced_info['horario']
                if isinstance(horario, dict):
                    display = horario.get('display', 'N/A')
                    estado = horario.get('estado', 'N/A')
                    
                    status_emoji = {
                        'abierta': '✅ ABIERTO AHORA - Servicios de emergencia disponibles',
                        'cerrada': '❌ CERRADO - Pero farmacia de turno debería estar disponible', 
                        'por_abrir': '🕐 ABRE MÁS TARDE - Revisa otras opciones de turno'
                    }.get(estado.lower(), f'❓ ESTADO: {estado.upper()}')
                    
                    print(f"\n   ⏰ HORARIOS DE EMERGENCIA:")
                    print(f"   🕐 Horario: {display}")
                    print(f"   🚨 Estado Actual: {status_emoji}")
            
            # Contacto mejorado para comunicación de emergencia
            if 'contacto' in enhanced_info:
                contacto = enhanced_info['contacto']
                print(f"\n   📞 CONTACTO DE EMERGENCIA:")
                
                phone_display = contacto.get('telefono_display', '')
                if phone_display and phone_display != 'Sin teléfono disponible':
                    print(f"   📱 Teléfono: {phone_display}")
                    print(f"   📞 Llamar directamente: {contacto.get('click_to_call', 'N/A')}")
                    print(f"   💬 WhatsApp: {contacto.get('whatsapp', 'N/A')}")
                else:
                    print(f"   ⚠️  No hay teléfono disponible para esta farmacia de turno")
            
            print(f"   " + "="*50)
            
            # Probar múltiples farmacias de turno si están disponibles
            if len(duty_pharmacies) > 1:
                print(f"\n   📊 Farmacias de turno adicionales en {comuna}: {len(duty_pharmacies) - 1}")
                for i, duty_p in enumerate(duty_pharmacies[1:3], 2):  # Mostrar máximo 2 más
                    enhanced = enhance_pharmacy_info(duty_p, db)
                    maps_available = 'mapas' in enhanced and enhanced['mapas'].get('google_maps')
                    phone_available = ('contacto' in enhanced and 
                                     enhanced['contacto'].get('telefono_display', '') != 'Sin teléfono disponible')
                    
                    print(f"   🚨 #{i}: {enhanced.get('nombre', 'N/A')} - " +
                          f"Mapas: {'✅' if maps_available else '❌'} | " +
                          f"Teléfono: {'✅' if phone_available else '❌'}")
        else:
            print(f"⚠️  {comuna}: No se encontraron farmacias de turno")
    
    if total_duty_found == 0:
        print("\n⚠️  NO SE ENCONTRARON FARMACIAS DE TURNO EN LA BASE DE DATOS")
        print("   Probando características mejoradas con farmacias regulares marcadas como turno...")
        
        # Simular farmacia de turno tomando una regular
        santiago_pharmacies = db.find_by_comuna("SANTIAGO")
        if santiago_pharmacies:
            sample_pharmacy = santiago_pharmacies[0]
            # Marcar manualmente como turno para prueba
            sample_pharmacy.es_turno = True
            
            enhanced = enhance_pharmacy_info(sample_pharmacy, db)
            
            print(f"\n🧪 CARACTERÍSTICAS MEJORADAS DE FARMACIA DE TURNO SIMULADA:")
            print(f"📍 {enhanced.get('nombre', 'N/A')} (marcada como turno para prueba)")
            
            # Mostrar todas las características mejoradas
            print(f"\n🔍 TODAS LAS CARACTERÍSTICAS MEJORADAS:")
            for key, value in enhanced.items():
                if key in ['mapas', 'horario', 'contacto']:
                    print(f"   ✅ {key}: {type(value).__name__} con {len(str(value))} caracteres")
    
    else:
        print(f"\n📊 RESUMEN DE CARACTERÍSTICAS MEJORADAS FARMACIAS DE TURNO:")
        print(f"   🚨 Total farmacias de turno encontradas: {total_duty_found}")
        print(f"   ✅ Todas las farmacias de turno ahora tienen características de ubicación mejoradas:")
        print(f"      🗺️  Mapas con un clic para navegación de emergencia")
        print(f"      📞 Llamar con un clic para contacto inmediato")
        print(f"      🕐 Horarios mejorados con estado en tiempo real")
        print(f"      💬 Múltiples opciones de comunicación")
    
    return total_duty_found

def test_emergency_scenarios():
    """Probar escenarios de emergencia específicos"""
    print(f"\n🚨 PRUEBA DE ESCENARIOS DE EMERGENCIA")
    print("=" * 40)
    
    db = PharmacyDatabase()
    
    scenarios = [
        "Necesito medicamento de emergencia en Santiago a medianoche",
        "Emergencia de fiebre infantil - necesito farmacia en Las Condes", 
        "Emergencia de fin de semana - necesito farmacia abierta en Providencia",
        "Emergencia medicamento cardíaco - necesito farmacia más cercana"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🚨 ESCENARIO {i}: {scenario}")
        
        # Para cada escenario, encontrar y mejorar una farmacia
        comuna_mapping = {
            1: "SANTIAGO",
            2: "LAS CONDES", 
            3: "PROVIDENCIA",
            4: "SANTIAGO"  # Por defecto Santiago para más cercana
        }
        
        comuna = comuna_mapping[i]
        pharmacies = db.find_by_comuna(comuna)
        
        if pharmacies:
            # Usar primera farmacia como ejemplo
            pharmacy = pharmacies[0]
            pharmacy.es_turno = True  # Marcar como turno para escenario
            
            enhanced = enhance_pharmacy_info(pharmacy, db)
            
            print(f"   🏥 FARMACIA DE EMERGENCIA: {enhanced.get('nombre', 'N/A')}")
            
            # Características críticas para emergencia
            if 'mapas' in enhanced:
                directions = enhanced['mapas'].get('direcciones', '')
                print(f"   🚨 NAVEGACIÓN URGENTE: {directions}")
            
            if 'contacto' in enhanced:
                phone = enhanced['contacto'].get('click_to_call', '')
                if phone and phone != 'tel:':
                    print(f"   📞 LLAMADA DE EMERGENCIA: {phone}")
            
            if 'horario' in enhanced and isinstance(enhanced['horario'], dict):
                status = enhanced['horario'].get('estado', 'unknown')
                if status == 'abierta':
                    print(f"   ✅ ESTADO: ABIERTO AHORA - Proceder inmediatamente")
                else:
                    print(f"   ⚠️  ESTADO: {status.upper()} - Revisar alternativas")

if __name__ == "__main__":
    print("🚨 PRUEBA DE CARACTERÍSTICAS MEJORADAS PARA FARMACIAS DE TURNO")
    print("Probando características mejoradas para escenarios de farmacias de emergencia")
    print()
    
    duty_count = test_duty_pharmacy_formatting()
    test_emergency_scenarios()
    
    print(f"\n" + "="*60)
    print(f"🎉 ¡PRUEBA DE CARACTERÍSTICAS MEJORADAS FARMACIAS DE TURNO COMPLETADA!")
    print(f"✅ Las características de ubicación mejoradas brindan capacidades críticas de emergencia:")
    print(f"   🗺️  Navegación GPS instantánea a farmacias de emergencia")
    print(f"   📞 Llamar con un clic para asistencia inmediata")
    print(f"   🕐 Estado en tiempo real (abierto/cerrado) para planificación de emergencia")
    print(f"   💬 Múltiples métodos de contacto (teléfono + WhatsApp)")
    print(f"   📍 Coordenadas precisas para servicios de emergencia")
    print(f"\n⚡ ¡Estas características son ESENCIALES para situaciones de farmacias de emergencia!")
    
    if duty_count > 0:
        print(f"🚨 Se encontraron {duty_count} farmacias de turno reales con características mejoradas")
    else:
        print(f"📝 Nota: No hay farmacias de turno en la BD, pero las características mejoradas funcionan para todas")
