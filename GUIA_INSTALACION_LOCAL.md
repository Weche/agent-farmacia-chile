# 🚀 GUÍA COMPLETA: EJECUTAR AGENTE FARMACIA CHILE LOCALMENTE

## 📋 REQUISITOS PREVIOS

### 1. **Software Base**
- **Python 3.8+** (recomendado 3.11+)
- **Git** para clonar el repositorio
- **Redis** para caché y sesiones (ver opciones abajo)

### 2. **APIs Requeridas**
- **OpenAI API Key** - Para el agente GPT-3.5-turbo
- **Langfuse Account** - Para observabilidad (opcional pero recomendado)

---

## 🎯 INSTALACIÓN PASO A PASO

### **PASO 1: Clonar el Repositorio**
```bash
git clone https://github.com/Weche/agent-farmacia-chile.git
cd agent-farmacia-chile
```

### **PASO 2: Configurar Entorno Virtual**
```bash
# Crear entorno virtual
python -m venv farmacia_env

# Activar (Windows)
farmacia_env\Scripts\activate

# Activar (Linux/Mac)
source farmacia_env/bin/activate
```

### **PASO 3: Instalar Dependencias**
```bash
pip install -r requirements.txt
```

### **PASO 4: Configurar Redis**

**📦 OPCIÓN A: Redis Local (Recomendado)**
```bash
# Windows (con Chocolatey)
choco install redis-64
redis-server

# Windows (con WSL)
sudo apt update && sudo apt install redis-server
redis-server

# Mac (con Homebrew)
brew install redis
redis-server

# Docker (cualquier OS)
docker run -d -p 6379:6379 redis:alpine
```

**☁️ OPCIÓN B: Redis Cloud (Más fácil)**
1. Ir a [Redis Cloud](https://redis.com/redis-enterprise-cloud/)
2. Crear cuenta gratuita (30MB gratis)
3. Crear database
4. Copiar URL de conexión

### **PASO 5: Configurar Variables de Entorno**
```bash
# Copiar template
cp .env.example .env

# Editar .env con tus valores
```

**📝 Ejemplo de .env configurado:**
```bash
# Application Settings
APP_NAME="Farmacias de Turno + Vademécum (MVP v2)"
ENV="dev"

# Redis (OBLIGATORIO)
REDIS_URL="redis://localhost:6379"
# O si usas Redis Cloud:
# REDIS_URL="rediss://default:tu_password@tu-redis-url.com:port"

# AI Agent (OBLIGATORIO)
OPENAI_API_KEY="sk-tu-clave-de-openai-aqui"
AGENT_MODEL="gpt-3.5-turbo"
AGENT_TEMPERATURE="0.1"

# Langfuse (OPCIONAL - para observabilidad)
LANGFUSE_PUBLIC_KEY="pk_lf_..."
LANGFUSE_SECRET_KEY="sk_lf_..."
LANGFUSE_HOST="https://cloud.langfuse.com"
LANGFUSE_ENABLED="true"
```

---

## 🚀 EJECUTAR LA APLICACIÓN

### **OPCIÓN 1: Desarrollo (con auto-reload)**
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload
```

### **OPCIÓN 2: Producción local**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003
```

### **OPCIÓN 3: Con Docker**
```bash
# Construir imagen
docker build -t farmacia-chile .

# Ejecutar contenedor
docker run -p 8003:8003 --env-file .env farmacia-chile
```

---

## 🔗 ACCEDER A LA APLICACIÓN

Una vez ejecutando, abre tu navegador en:

- **🌐 Frontend Principal**: http://localhost:8003
- **🤖 Chat Interface**: http://localhost:8003 (esquina inferior derecha)
- **📚 API Docs**: http://localhost:8003/docs
- **📊 Status**: http://localhost:8003/status

---

## ✅ VERIFICAR QUE TODO FUNCIONA

### **Test 1: Health Check**
```bash
curl http://localhost:8003/status
```

### **Test 2: Chat API**
```bash
curl -X POST "http://localhost:8003/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hola, busco farmacias en Las Condes"}'
```

### **Test 3: Frontend Chat**
1. Abrir http://localhost:8003
2. Hacer clic en el chat (esquina inferior derecha)
3. Escribir: "¿Hay farmacias abiertas en Providencia?"

---

## 🎯 ENDPOINTS PRINCIPALES

### **Frontend**
- `GET /` - Página principal con chat
- `GET /status` - Estado del sistema

### **Chat API (Agente Español)**
- `POST /chat` - Chat simple
- `POST /api/chat/session` - Crear sesión
- `POST /api/chat/message` - Enviar mensaje
- `GET /api/chat/history/{session_id}` - Obtener historial

### **Legacy API**
- `GET /farmacias` - Búsqueda directa (sin IA)
- `GET /comunas` - Lista de comunas

---

## 🔧 TROUBLESHOOTING

### **❌ Error: Redis Connection**
```bash
# Verificar que Redis esté ejecutándose
redis-cli ping
# Debe responder: PONG

# Si no funciona, iniciar Redis
redis-server
```

### **❌ Error: OpenAI API**
```bash
# Verificar API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer tu-api-key-aqui"
```

### **❌ Error: Port 8003 en uso**
```bash
# Cambiar puerto
python -m uvicorn app.main:app --host 127.0.0.1 --port 8004 --reload
```

### **❌ Error: Imports**
```bash
# Ejecutar desde raíz del proyecto
cd agent-farmacia-chile
python -m uvicorn app.main:app --reload
```

---

## 🚨 CONFIGURACIÓN MÍNIMA PARA TESTING

Si solo quieres probar rápidamente:

```bash
# .env mínimo
REDIS_URL="redis://localhost:6379"
OPENAI_API_KEY="tu-api-key"
LANGFUSE_ENABLED="false"
```

---

## 🎉 ¡LISTO!

Con esto deberías tener el **Agente Farmacia Chile** ejecutándose localmente con:

- ✅ **Chat IA en español** funcionando
- ✅ **Búsqueda inteligente** de farmacias
- ✅ **Sistema LLM + embeddings** activo
- ✅ **Frontend moderno** con interfaz chat
- ✅ **APIs completas** documentadas

---

## 📞 SOPORTE

Si tienes problemas:
1. Verificar que Redis esté ejecutándose
2. Confirmar que OpenAI API key es válida
3. Revisar logs en la terminal
4. Consultar `/docs` para API reference

¡El agente está listo para conversar en español sobre farmacias! 🇨🇱💊
