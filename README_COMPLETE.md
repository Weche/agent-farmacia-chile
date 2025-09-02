# 🏥 Pharmacy Finder - Complete Setup Guide

> 📋 **This is the detailed setup and configuration guide. For project overview, features, and quick start, see [`README.md`](README.md)**

## 📋 Project Overview

This is a comprehensive pharmacy finder application for Chile that includes:

- **FastAPI Backend** - REST API for pharmacy data
- **SQLite Database** - Local storage for pharmacy information  
- **Redis Cloud Cache** - Ultra-fast responses with smart invalidation (NEW)
- **Web Interface** - Interactive map-based pharmacy finder
- **MINSAL Integration** - Real-time data from Chile's Ministry of Health
- **Quality Monitoring** - Automated data freshness and API health checks

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd pharmacy-finder
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy and edit environment file
copy .env.example .env

# The .env file should contain:
APP_NAME="Farmacias de Turno + Vademécum (MVP v2)"
ENV="dev"
MINSAL_API_BASE="https://midas.minsal.cl/farmacia_v2/WS"
HTTP_TIMEOUT="8.0"
VADEMECUM_PATH="./data/vademecum_clean.parquet"

# Redis Cache Configuration (NEW)
REDIS_URL="redis://default:password@host:port"

# Cache TTL Settings (seconds)
CACHE_TTL_CRITICAL=300      # 5 minutes - turno pharmacies, open status
CACHE_TTL_HIGH=1800         # 30 minutes - search results, stats  
CACHE_TTL_MEDIUM=21600      # 6 hours - commune lists
CACHE_TTL_LOW=86400         # 24 hours - static data

# Cache Invalidation Settings
AUTO_INVALIDATE_ON_DB_CHANGE=true
CHECK_MINSAL_API_UPDATES=true
CACHE_HEALTH_CHECK_INTERVAL=60

# Fallback Settings
FALLBACK_TO_SQLITE=true
SERVE_STALE_ON_ERROR=true
MAX_STALE_AGE_SECONDS=3600  # 1 hour max stale data
```

## 🚀 Redis Cloud Setup (NEW)

### **Getting Redis Cloud Instance**
1. Sign up at [Redis Cloud](https://redis.com/try-free/)
2. Create a free database (up to 30MB)
3. Get connection string: `redis://default:password@host:port`
4. Add to your `.env` file as `REDIS_URL`

### **Redis Configuration Options**
```bash
# Basic Redis connection
REDIS_URL="redis://localhost:6379"  # Local Redis

# Redis Cloud with authentication
REDIS_URL="redis://default:password@host:port"  # Cloud Redis

# Redis with SSL (production)
REDIS_URL="rediss://default:password@host:port"  # SSL enabled
```

### **Testing Redis Connection**
```bash
# Test Redis connectivity
python test_redis.py

# Test cache performance
python test_cache_server.py

# Check cache health via API
curl http://127.0.0.1:8000/api/cache/health
```

### 3. Import Pharmacy Data
```bash
python import_data.py
```
This will:
- Fetch data from MINSAL API
- Create SQLite database (`pharmacy_finder.db`)
- Import 2,800+ pharmacies
- Show statistics and test Villa Alemana

### 4. Start the Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Access the Application
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🗂️ Project Structure

```
pharmacy-finder/
├── app/
│   ├── main.py              # FastAPI application
│   ├── services/
│   │   ├── minsal_client.py # MINSAL API client
│   │   └── vademecum_service.py # Medicine database
│   └── core/
│       └── utils.py         # Utility functions
├── templates/
│   └── index.html           # Web interface
├── database.py              # Database models
├── import_data.py           # Data import script
├── explore_data.py          # Data exploration
├── test_web.py             # Web interface test
├── pharmacy_finder.db      # SQLite database (created)
├── requirements.txt
├── .env                    # Environment config
└── README.md
```

## 🗃️ Database Schema

### Pharmacies Table
```sql
CREATE TABLE pharmacies (
    local_id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    direccion TEXT,
    comuna TEXT,
    localidad TEXT,
    region TEXT,
    telefono TEXT,
    lat REAL,
    lng REAL,
    hora_apertura TEXT,
    hora_cierre TEXT,
    dia_funcionamiento TEXT,
    fecha_actualizacion TEXT,
    es_turno BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Key Features
- **2,802 pharmacies** across Chile
- **257 communes** covered
- **119 pharmacies** currently on duty
- **Geographic coordinates** for mapping
- **Real-time updates** from MINSAL

## 🌐 Web Interface Features

### Search & Filter
- 🔍 Search by commune (e.g., "santiago", "valparaíso")
- 🟢 Filter for pharmacies currently open
- 📍 Location-based search with geolocation

### Interactive Map
- 🗺️ OpenStreetMap integration
- 📌 Pharmacy markers with custom icons
- 🟢 Green markers for pharmacies on duty
- 🔵 Blue markers for regular pharmacies
- 📱 Responsive design

### Pharmacy Information
- 📍 Address and location
- 📞 Phone number
- 🕐 Opening hours
- 🏙️ Commune and region
- 🟢 Turn status indicator

## 🔌 API Endpoints

### Existing Endpoints
- `GET /health` - Health check
- `GET /farmacias` - Search pharmacies
- `GET /medicamentos` - Search medicines
- `POST /chat` - AI chat interface

### New Endpoints
- `GET /` - Web interface
- `GET /api/stats` - Database statistics
- `GET /api/nearby` - Nearby pharmacies
- `GET /api/communes` - List of communes

## 📊 Data Management

### Import Process
```python
from database import PharmacyDatabase
from import_data import MINSALDataImporter

# Initialize database
db = PharmacyDatabase()

# Import data
importer = MINSALDataImporter(db)
importer.import_all_pharmacies()
```

### Query Examples
```python
# Find pharmacies in a commune
pharmacies = db.find_by_comuna("santiago", only_open=True)

# Find nearby pharmacies
pharmacies = db.find_nearby_pharmacies(-33.4489, -70.6693, radius_km=5)

# Get statistics
stats = db.get_pharmacy_count()
```

## 🧪 Testing

### Test Data Import
```bash
python import_data.py
```

### Test Web Interface
```bash
python test_web.py
```

### Test Specific Location
```bash
python -c "
from database import PharmacyDatabase
db = PharmacyDatabase()
pharmacies = db.find_by_comuna('villa alemana', True)
print(f'Found {len(pharmacies)} pharmacies')
for p in pharmacies[:3]:
    print(f'- {p.nombre}: {p.direccion}')
"
```

## 🔧 Configuration

### Environment Variables
```bash
# Application
APP_NAME="Farmacias de Turno + Vademécum (MVP v2)"
ENV="dev"

# MINSAL API
MINSAL_API_BASE="https://midas.minsal.cl/farmacia_v2/WS"
HTTP_TIMEOUT="8.0"

# Data
VADEMECUM_PATH="./data/vademecum_clean.parquet"
```

### Database Configuration
- **File**: `pharmacy_finder.db`
- **Type**: SQLite
- **Location**: Project root
- **Auto-created** on first import

## 🚨 Troubleshooting

### Server Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi

# Check imports
python -c "from app.main import app; print('OK')"
```

### No Data in Database
```bash
# Re-import data
python import_data.py

# Check database
python -c "
from database import PharmacyDatabase
db = PharmacyDatabase()
print('Stats:', db.get_pharmacy_count())
"
```

### Map Not Loading
- Check internet connection for OpenStreetMap tiles
- Verify pharmacy coordinates are valid
- Check browser console for JavaScript errors

## 🎯 Usage Examples

### Find Pharmacies in Santiago
```
Search: "santiago"
Filter: "Solo de turno"
```

### Use Geolocation
1. Click "📍 Mi Ubicación"
2. Allow location permission
3. See nearby pharmacies on map

### API Usage
```bash
# Get pharmacies in a commune
curl "http://localhost:8000/farmacias?comuna=santiago&abierto=true"

# Get nearby pharmacies
curl "http://localhost:8000/api/nearby?lat=-33.4489&lng=-70.6693&radius=5"
```

## 📈 Future Enhancements

- [ ] Add pharmacy photos
- [ ] Implement user favorites
- [ ] Add route planning
- [ ] Push notifications for nearby pharmacies
- [ ] Offline map support
- [ ] Multi-language support

## 📝 Notes

- Data is updated from MINSAL's official API
- Coordinates may have minor inaccuracies
- Opening hours are provided by MINSAL
- This is for informational purposes only

---

**Made with ❤️ for Chilean healthcare accessibility**
