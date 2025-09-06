@echo off
REM 🚀 SETUP AUTOMÁTICO - Agente Farmacia Chile (Windows)
REM Ejecuta: setup_local.bat

echo 🚀 INICIANDO SETUP DEL AGENTE FARMACIA CHILE...
echo ================================================

REM Verificar Python
echo 📦 Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado. Por favor instala Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python encontrado

REM Crear entorno virtual
echo 📦 Creando entorno virtual...
python -m venv farmacia_env
call farmacia_env\Scripts\activate.bat
echo ✅ Entorno virtual creado y activado

REM Instalar dependencias
echo 📦 Instalando dependencias...
pip install -r requirements.txt
echo ✅ Dependencias instaladas

REM Verificar Redis
echo 🔄 Verificando Redis...
redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Redis está ejecutándose
) else (
    echo ⚠️  Redis no encontrado o no ejecutándose
    echo 👉 Opciones para Redis:
    echo    - Windows: choco install redis-64
    echo    - Docker: docker run -d -p 6379:6379 redis:alpine
    echo    - Redis Cloud: https://redis.com/redis-enterprise-cloud/
)

REM Configurar .env
echo 📝 Configurando variables de entorno...
if not exist .env (
    copy .env.example .env
    echo ✅ Archivo .env creado desde template
    echo 👉 IMPORTANTE: Edita .env con tu OpenAI API key
    echo 👉 Mínimo requerido:
    echo    - OPENAI_API_KEY='tu-api-key'
    echo    - REDIS_URL='redis://localhost:6379'
) else (
    echo ✅ Archivo .env ya existe
)

REM Verificar estructura
echo 🔍 Verificando estructura del proyecto...
if exist "app\main.py" (
    echo ✅ Estructura del proyecto correcta
) else (
    echo ❌ Estructura incorrecta. ¿Estás en la raíz del proyecto?
    pause
    exit /b 1
)

echo.
echo 🎉 SETUP COMPLETADO!
echo ====================
echo.
echo 🚀 PRÓXIMOS PASOS:
echo 1. Editar .env con tu OpenAI API key
echo 2. Asegurar que Redis esté ejecutándose
echo 3. Ejecutar: python -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload
echo 4. Abrir: http://localhost:8003
echo.
echo 📚 Ver guía completa: GUIA_INSTALACION_LOCAL.md
echo.
pause
