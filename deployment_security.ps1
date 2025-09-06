# deployment_security.ps1
# Script para configurar autenticación segura en producción

Write-Host "🔐 Configuración de Seguridad para Deployment" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Generar clave runtime aleatoria segura
$bytes = New-Object byte[] 32
(New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
$RUNTIME_KEY = [Convert]::ToBase64String($bytes)

Write-Host ""
Write-Host "📋 CONFIGURACIÓN PARA PRODUCCIÓN:" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Yellow

Write-Host ""
Write-Host "1️⃣ Variables de entorno para Windows:" -ForegroundColor Cyan
Write-Host "`$env:ADMIN_USERNAME='tu_usuario_admin'"
Write-Host "`$env:ADMIN_PASSWORD='tu_contraseña_super_segura'"
Write-Host "`$env:RUNTIME_ADMIN_KEY='$RUNTIME_KEY'"

Write-Host ""
Write-Host "2️⃣ Para Docker/Docker-compose, agregar al .env:" -ForegroundColor Cyan
Write-Host "ADMIN_USERNAME=tu_usuario_admin"
Write-Host "ADMIN_PASSWORD=tu_contraseña_super_segura"
Write-Host "RUNTIME_ADMIN_KEY=$RUNTIME_KEY"

Write-Host ""
Write-Host "3️⃣ Para Fly.io deployment:" -ForegroundColor Cyan
Write-Host "fly secrets set ADMIN_USERNAME=tu_usuario_admin"
Write-Host "fly secrets set ADMIN_PASSWORD=tu_contraseña_super_segura"
Write-Host "fly secrets set RUNTIME_ADMIN_KEY=$RUNTIME_KEY"

Write-Host ""
Write-Host "🛡️ NOTAS DE SEGURIDAD:" -ForegroundColor Red
Write-Host "======================" -ForegroundColor Red
Write-Host "• NUNCA commitear las credenciales reales al repositorio"
Write-Host "• La RUNTIME_ADMIN_KEY tiene precedencia sobre otras claves"
Write-Host "• Cambiar credenciales regularmente"
Write-Host "• Usar HTTPS en producción siempre"

Write-Host ""
Write-Host "✅ Runtime Key generada: " -ForegroundColor Green -NoNewline
Write-Host "$RUNTIME_KEY" -ForegroundColor White
Write-Host "⚠️  GUARDAR ESTA CLAVE DE FORMA SEGURA" -ForegroundColor Yellow

# Crear .env.production de ejemplo
$envContent = @"
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
"@

$envContent | Out-File -FilePath ".env.production.example" -Encoding UTF8

Write-Host ""
Write-Host "📄 Creado: .env.production.example" -ForegroundColor Green
Write-Host "   Copiar y completar para tu deployment"
