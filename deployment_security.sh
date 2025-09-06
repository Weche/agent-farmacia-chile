#!/bin/bash
# deployment_security.sh
# Script para configurar autenticación segura en producción

echo "🔐 Configuración de Seguridad para Deployment"
echo "============================================="

# Generar clave runtime aleatoria segura
RUNTIME_KEY=$(openssl rand -base64 32)

echo ""
echo "📋 CONFIGURACIÓN PARA PRODUCCIÓN:"
echo "================================="

echo ""
echo "1️⃣ Variables de entorno requeridas:"
echo "export ADMIN_USERNAME='tu_usuario_admin'"
echo "export ADMIN_PASSWORD='tu_contraseña_super_segura'"
echo "export RUNTIME_ADMIN_KEY='$RUNTIME_KEY'"

echo ""
echo "2️⃣ Para Docker/Docker-compose, agregar al .env:"
echo "ADMIN_USERNAME=tu_usuario_admin"
echo "ADMIN_PASSWORD=tu_contraseña_super_segura"
echo "RUNTIME_ADMIN_KEY=$RUNTIME_KEY"

echo ""
echo "3️⃣ Para Fly.io deployment:"
echo "fly secrets set ADMIN_USERNAME=tu_usuario_admin"
echo "fly secrets set ADMIN_PASSWORD=tu_contraseña_super_segura"
echo "fly secrets set RUNTIME_ADMIN_KEY=$RUNTIME_KEY"

echo ""
echo "4️⃣ Para Railway/Render/Vercel:"
echo "Configurar en las variables de entorno del dashboard:"
echo "- ADMIN_USERNAME: tu_usuario_admin"
echo "- ADMIN_PASSWORD: tu_contraseña_super_segura"
echo "- RUNTIME_ADMIN_KEY: $RUNTIME_KEY"

echo ""
echo "🛡️ NOTAS DE SEGURIDAD:"
echo "======================"
echo "• NUNCA commitear las credenciales reales al repositorio"
echo "• La RUNTIME_ADMIN_KEY tiene precedencia sobre otras claves"
echo "• Cambiar credenciales regularmente"
echo "• Usar HTTPS en producción siempre"

echo ""
echo "✅ Runtime Key generada: $RUNTIME_KEY"
echo "⚠️  GUARDAR ESTA CLAVE DE FORMA SEGURA"

# Crear .env.production de ejemplo
cat > .env.production.example << EOL
# Archivo de ejemplo para producción - NO COMMITEAR ESTE ARCHIVO CON VALORES REALES
# Copiar a .env.production y completar con valores reales

# Database & Redis (configurar según tu deployment)
REDIS_URL="redis://tu-redis-url"

# OpenAI
OPENAI_API_KEY="tu-openai-key"

# Google Maps (opcional)
GOOGLE_MAPS_API_KEY="tu-google-maps-key"

# Session Management
SESSION_EXPIRY_HOURS="2"
MAX_CONVERSATION_LENGTH="50"
SESSION_CLEANUP_INTERVAL="3600"

# Admin Security (CONFIGURAR ESTOS VALORES)
ADMIN_USERNAME="tu_usuario_admin"
ADMIN_PASSWORD="tu_contraseña_super_segura"
RUNTIME_ADMIN_KEY="$RUNTIME_KEY"

# NO usar estas claves en producción (solo para desarrollo)
# ADMIN_KEY="PharmacyAdmin2024!"

# Langfuse (opcional)
LANGFUSE_PUBLIC_KEY=""
LANGFUSE_SECRET_KEY=""
LANGFUSE_HOST=""
LANGFUSE_ENABLED="false"
EOL

echo ""
echo "📄 Creado: .env.production.example"
echo "   Copiar y completar para tu deployment"
