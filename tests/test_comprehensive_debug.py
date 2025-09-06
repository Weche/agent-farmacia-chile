"""
Diagnóstico Completo - Enlaces No Clickeables en Chat
Múltiples estrategias para identificar el problema real
"""

import requests
import json
from datetime import datetime

def test_1_raw_api_response():
    """Test 1: Verificar respuesta cruda de la API"""
    print("🔍 TEST 1: RESPUESTA CRUDA DE LA API")
    print("=" * 50)
    
    try:
        response = requests.post(
            "http://127.0.0.1:8003/api/chat",
            json={"message": "emergencia maipu necesito direcciones"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            
            print(f"📝 Respuesta completa:")
            print(f"   Status: {response.status_code}")
            print(f"   Length: {len(message)} caracteres")
            print(f"   Contains [text](url): {'[' in message and '](' in message}")
            print(f"   Contains <a href: {'<a href' in message}")
            print(f"   Raw message preview:")
            print(f"   {message[:200]}...")
            
            return message
        else:
            print(f"❌ Error API: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando API: {e}")
        return None

def test_2_javascript_simulation():
    """Test 2: Simular exactamente lo que hace JavaScript"""
    print(f"\n🔍 TEST 2: SIMULACIÓN JAVASCRIPT")
    print("=" * 50)
    
    # Simular respuesta típica
    raw_response = """Encontré 3 farmacias de turno en Maipú:

1. 🏪 FARMAQUINTA
📍 Dirección: AVENIDA VALPARAISO 1621, VILLA ALEMANA
📞 Teléfono: +56 79 859 135
⏰ Horario: Viernes 00:00 - 23:59
🌐 [Ver en Google Maps](https://maps.google.com/maps?q=-33.0449112,-71.3856936)

2. 🏪 BELLFARMA
📍 Dirección: HUANHUALI 1331, VILLA ALEMANA
📞 Teléfono: +563118844
⏰ Horario: Sábado 09:00 - 18:00 (Por abrir)
🌐 [Ver en Google Maps](https://maps.google.com/maps?q=-33.058657929509,-71.3860337445243)"""
    
    # Simular escapeHtml (básico)
    import html
    escaped = html.escape(raw_response)
    print(f"📝 Después de escapeHtml:")
    print(f"   Length: {len(escaped)}")
    print(f"   Contains &lt;: {'&lt;' in escaped}")
    print(f"   Preview: {escaped[:100]}...")
    
    # Simular conversión de saltos de línea
    with_br = escaped.replace('\n', '<br>')
    print(f"\n📄 Después de \\n -> <br>:")
    print(f"   Length: {len(with_br)}")
    print(f"   Contains <br>: {'<br>' in with_br}")
    
    # Simular conversión de enlaces Markdown
    import re
    markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(markdown_pattern, with_br)
    print(f"\n🔗 Patrones Markdown encontrados: {len(matches)}")
    
    if matches:
        for i, (text, url) in enumerate(matches, 1):
            print(f"   {i}. '{text}' -> '{url}'")
    
    # Aplicar conversión
    converted = re.sub(markdown_pattern, r'<a href="\2" target="_blank" class="pharmacy-link">\1</a>', with_br)
    print(f"\n✅ Después de conversión a HTML:")
    print(f"   Length: {len(converted)}")
    print(f"   Contains <a href: {'<a href' in converted}")
    print(f"   Contains pharmacy-link: {'pharmacy-link' in converted}")
    
    # Mostrar ejemplo de enlace generado
    link_match = re.search(r'<a href="[^"]*" target="_blank" class="pharmacy-link">[^<]*</a>', converted)
    if link_match:
        print(f"   Ejemplo enlace: {link_match.group()}")
    
    return converted

def test_3_browser_console_debug():
    """Test 3: Código para debuggear en consola del navegador"""
    print(f"\n🔍 TEST 3: CÓDIGO PARA CONSOLA DEL NAVEGADOR")
    print("=" * 50)
    
    console_code = """
// 🔍 COPIAR Y PEGAR ESTO EN LA CONSOLA DEL NAVEGADOR:

console.log("🔍 DEBUGGING CHAT LINKS");

// 1. Verificar si ChatManager existe
console.log("1. ChatManager exists:", typeof window.chatManager !== 'undefined');

// 2. Revisar último mensaje en DOM
const lastMessage = document.querySelector('.ai-message-main:last-child .message-content-main');
if (lastMessage) {
    console.log("2. Last AI message HTML:", lastMessage.innerHTML);
    console.log("3. Contains <a> tags:", lastMessage.innerHTML.includes('<a href'));
    console.log("4. Links found:", lastMessage.querySelectorAll('a').length);
    
    // Verificar cada enlace
    const links = lastMessage.querySelectorAll('a');
    links.forEach((link, i) => {
        console.log(`   Link ${i+1}:`, {
            href: link.href,
            text: link.textContent,
            classes: link.className,
            target: link.target
        });
    });
} else {
    console.log("2. ❌ No AI message found");
}

// 3. Test formatAIResponse function directly
if (window.chatManager && window.chatManager.formatAIResponse) {
    const testInput = "Test [Google Maps](https://maps.google.com/test)";
    const formatted = window.chatManager.formatAIResponse(testInput);
    console.log("5. formatAIResponse test:");
    console.log("   Input:", testInput);
    console.log("   Output:", formatted);
    console.log("   Contains <a>:", formatted.includes('<a href'));
}

// 4. Verificar CSS
const testLink = document.createElement('a');
testLink.className = 'pharmacy-link';
testLink.href = 'https://test.com';
testLink.textContent = 'Test Link';
document.body.appendChild(testLink);
const styles = window.getComputedStyle(testLink);
console.log("6. CSS styles for .pharmacy-link:");
console.log("   Color:", styles.color);
console.log("   Background:", styles.background);
console.log("   Padding:", styles.padding);
document.body.removeChild(testLink);
"""
    
    print("📋 Código para pegar en consola del navegador:")
    print(console_code)
    
    return console_code

def test_4_direct_html_injection():
    """Test 4: Crear endpoint de testing directo"""
    print(f"\n🔍 TEST 4: ENDPOINT DE TESTING DIRECTO")
    print("=" * 50)
    
    test_endpoint_code = '''
# Agregar esto temporalmente a main.py para testing:

@app.get("/test-links")
async def test_links():
    """Endpoint para probar enlaces directamente"""
    test_html = """
    <div style="padding: 20px; font-family: Arial;">
        <h3>🔍 Test de Enlaces Clickeables</h3>
        
        <div class="ai-response-content">
            <p>Test 1: Enlace directo</p>
            <a href="https://maps.google.com/maps?q=-33.4489,-70.6693" target="_blank" class="pharmacy-link">📍 Google Maps Directo</a>
            
            <br><br>
            
            <p>Test 2: Enlace con estilos</p>
            <a href="tel:+56987654321" class="phone-link">📞 Llamar Test</a>
            
            <br><br>
            
            <p>Test 3: Información de farmacia</p>
            <div class="pharmacy-name">🏪 FARMACIA TEST</div>
            <div class="pharmacy-address">📍 Dirección Test 123</div>
            <div class="pharmacy-phone">📞 +56 9 8765 4321</div>
            <div class="pharmacy-hours">⏰ Lunes 08:00 - 18:00</div>
            <a href="https://maps.google.com/maps?q=-33.4489,-70.6693" target="_blank" class="pharmacy-link">🗺️ Ver en Maps</a>
        </div>
    </div>
    """
    return HTMLResponse(test_html)
'''
    
    print("📋 Código para agregar a main.py:")
    print(test_endpoint_code)
    print("\n📝 Después de agregar, visitar: http://127.0.0.1:8003/test-links")
    
    return test_endpoint_code

def test_5_check_css_loading():
    """Test 5: Verificar que CSS se carga correctamente"""
    print(f"\n🔍 TEST 5: VERIFICAR CARGA DE CSS")
    print("=" * 50)
    
    try:
        # Verificar que main.css se puede cargar
        css_response = requests.get("http://127.0.0.1:8003/templates/assets/css/main.css")
        
        if css_response.status_code == 200:
            css_content = css_response.text
            
            # Buscar nuestros estilos específicos
            checks = {
                'pharmacy-link': '.pharmacy-link' in css_content,
                'phone-link': '.phone-link' in css_content,
                'ai-response-content': '.ai-response-content' in css_content,
                'map-link': '.map-link' in css_content
            }
            
            print("📋 CSS Checks:")
            for style, found in checks.items():
                print(f"   {style}: {'✅' if found else '❌'}")
            
            if all(checks.values()):
                print("✅ Todos los estilos CSS están presentes")
            else:
                print("❌ Faltan algunos estilos CSS")
                
            return css_content
        else:
            print(f"❌ No se pudo cargar CSS: {css_response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error verificando CSS: {e}")
        return None

def test_6_check_js_loading():
    """Test 6: Verificar que JavaScript se carga correctamente"""
    print(f"\n🔍 TEST 6: VERIFICAR CARGA DE JAVASCRIPT")
    print("=" * 50)
    
    try:
        # Verificar que chat.js se puede cargar
        js_response = requests.get("http://127.0.0.1:8003/templates/assets/js/chat.js")
        
        if js_response.status_code == 200:
            js_content = js_response.text
            
            # Buscar funciones específicas
            checks = {
                'formatAIResponse': 'formatAIResponse(' in js_content,
                'markdown_regex': r'\[([^\]]+)\]\(([^)]+)\)' in js_content,
                'ai-response-content': 'ai-response-content' in js_content,
                'pharmacy-link_class': 'pharmacy-link' in js_content
            }
            
            print("📋 JavaScript Checks:")
            for func, found in checks.items():
                print(f"   {func}: {'✅' if found else '❌'}")
            
            if all(checks.values()):
                print("✅ Todas las funciones JavaScript están presentes")
            else:
                print("❌ Faltan algunas funciones JavaScript")
                
            return js_content
        else:
            print(f"❌ No se pudo cargar JavaScript: {js_response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error verificando JavaScript: {e}")
        return None

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO COMPLETO - ENLACES NO CLICKEABLES")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ejecutar todos los tests
    api_response = test_1_raw_api_response()
    js_simulation = test_2_javascript_simulation()
    console_code = test_3_browser_console_debug()
    endpoint_code = test_4_direct_html_injection()
    css_content = test_5_check_css_loading()
    js_content = test_6_check_js_loading()
    
    print(f"\n" + "="*60)
    print("🎯 RESUMEN DE DIAGNÓSTICO:")
    print(f"   1. API Response: {'✅' if api_response else '❌'}")
    print(f"   2. JS Simulation: ✅")  
    print(f"   3. Browser Debug Code: ✅")
    print(f"   4. Test Endpoint Code: ✅")
    print(f"   5. CSS Loading: {'✅' if css_content else '❌'}")
    print(f"   6. JS Loading: {'✅' if js_content else '❌'}")
    
    print(f"\n🔧 PRÓXIMOS PASOS:")
    print(f"   1. Ejecutar código en consola del navegador")
    print(f"   2. Agregar endpoint de testing si es necesario")
    print(f"   3. Verificar que archivos CSS/JS se cargan")
    print(f"   4. Revisar Network tab en DevTools")
    print(f"   5. Verificar errores en Console de navegador")
