"""
Debug Chat Link Formatting
Test the exact format of links being generated and processed
"""

# Test the exact text format that's being sent to the chat
sample_response = """Encontré 3 farmacias de turno en Maipú:

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

print("🔍 DEBUGGING CHAT LINK FORMAT")
print("=" * 50)
print("Raw response text:")
print(repr(sample_response))
print()

# Test the regex patterns from chat.js
import re

def test_markdown_links(text):
    """Test the markdown link regex"""
    # Pattern from chat.js: \[([^\]]+)\]\(([^)]+)\)
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, text)
    print(f"Markdown link matches found: {len(matches)}")
    for i, (link_text, url) in enumerate(matches, 1):
        print(f"  {i}. Text: '{link_text}' -> URL: '{url}'")
        # Show what the replacement would be
        replacement = f'<a href="{url}" target="_blank" class="pharmacy-link">{link_text}</a>'
        print(f"     Would become: {replacement}")
    return matches

def test_phone_links(text):
    """Test phone link detection"""
    pattern = r'\b(tel:\+\d+[0-9\-\s]*)'
    matches = re.findall(pattern, text)
    print(f"\nPhone link matches found: {len(matches)}")
    for match in matches:
        print(f"  Phone: {match}")

# Test with sample response
print("Testing regex patterns:")
markdown_matches = test_markdown_links(sample_response)
test_phone_links(sample_response)

# Test the full formatting function similar to JavaScript
def simulate_js_formatting(content):
    """Simulate the JavaScript formatAIResponse function"""
    import html
    
    # Escape HTML first (like JavaScript)
    formatted = html.escape(content)
    print(f"\n📝 After HTML escaping:")
    print(repr(formatted[:200]) + "...")
    
    # Convert line breaks
    formatted = formatted.replace('\n', '<br>')
    
    # Convert markdown links - MAIN TEST
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    before_count = len(re.findall(pattern, formatted))
    formatted = re.sub(pattern, r'<a href="\2" target="_blank" class="pharmacy-link">\1</a>', formatted)
    after_count = len(re.findall(r'<a href="[^"]*" target="_blank" class="pharmacy-link">[^<]*</a>', formatted))
    
    print(f"\n🔗 Markdown link conversion:")
    print(f"   Links found: {before_count}")
    print(f"   Links converted: {after_count}")
    
    # Show a sample of the result
    if 'pharmacy-link' in formatted:
        start_idx = formatted.find('<a href=')
        end_idx = formatted.find('</a>', start_idx) + 4
        sample = formatted[start_idx:end_idx] if start_idx >= 0 else "No links found"
        print(f"   Sample result: {sample}")
    
    return formatted

print("\n" + "="*50)
print("SIMULATING JAVASCRIPT FORMATTING:")
result = simulate_js_formatting(sample_response)

print(f"\n📊 Final result contains clickable links: {'pharmacy-link' in result}")
print(f"📊 Final result contains <a href: {'<a href=' in result}")

if '<a href=' in result:
    print("\n✅ Links should be clickable!")
    # Extract a sample link
    import re
    link_pattern = r'<a href="[^"]*"[^>]*>[^<]*</a>'
    links = re.findall(link_pattern, result)
    if links:
        print("Sample generated link:")
        print(f"  {links[0]}")
else:
    print("\n❌ Links are not being converted to clickable format")
    print("This explains why you still see markdown text!")
