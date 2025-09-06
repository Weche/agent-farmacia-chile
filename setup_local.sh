#!/bin/bash
# 🚀 SETUP AUTOMÁTICO - Agente Farmacia Chile
# Ejecuta: bash setup_local.sh

set -e

echo "🚀 INICIANDO SETUP DEL AGENTE FARMACIA CHILE..."
echo "================================================"

# Verificar Python
echo "📦 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado. Por favor instala Python 3.8+"
    exit 1
fi
echo "✅ Python encontrado: $(python3 --version)"

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv farmacia_env
source farmacia_env/bin/activate
echo "✅ Entorno virtual creado y activado"

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt
echo "✅ Dependencias instaladas"

# Verificar Redis
echo "🔄 Verificando Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis está ejecutándose"
    else
        echo "⚠️  Redis instalado pero no ejecutándose"
        echo "👉 Ejecuta: redis-server"
    fi
else
    echo "⚠️  Redis no encontrado"
    echo "👉 Instala Redis o usa Redis Cloud"
    echo "   - Mac: brew install redis"
    echo "   - Ubuntu: sudo apt install redis-server"
    echo "   - Docker: docker run -d -p 6379:6379 redis:alpine"
fi

# Configurar .env
echo "📝 Configurando variables de entorno..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Archivo .env creado desde template"
    echo "👉 IMPORTANTE: Edita .env con tu OpenAI API key"
    echo "👉 Mínimo requerido:"
    echo "   - OPENAI_API_KEY='tu-api-key'"
    echo "   - REDIS_URL='redis://localhost:6379'"
else
    echo "✅ Archivo .env ya existe"
fi

# Verificar estructura
echo "🔍 Verificando estructura del proyecto..."
if [ -f "app/main.py" ]; then
    echo "✅ Estructura del proyecto correcta"
else
    echo "❌ Estructura incorrecta. ¿Estás en la raíz del proyecto?"
    exit 1
fi

echo ""
echo "🎉 SETUP COMPLETADO!"
echo "===================="
echo ""
echo "🚀 PRÓXIMOS PASOS:"
echo "1. Editar .env con tu OpenAI API key"
echo "2. Asegurar que Redis esté ejecutándose"
echo "3. Ejecutar: python -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload"
echo "4. Abrir: http://localhost:8003"
echo ""
echo "📚 Ver guía completa: GUIA_INSTALACION_LOCAL.md"
echo ""
