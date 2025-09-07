# app/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os

from app.services.minsal_client import get_locales, get_locales_turno
from app.services.vademecum_service import load_vademecum, search_vademecum
from app.database import PharmacyDatabase
from app.core.enhanced_pharmacy_search import EnhancedPharmacyDatabase
from app.cache.redis_client import get_redis_client
from app.cache.invalidation import get_invalidation_manager, manual_cache_invalidation
from app.middleware.cache_middleware import CacheMiddleware, cache_warmup, cache_health_check
from app.agents.spanish_agent import SpanishPharmacyAgent
from app.status import router as status_router
import json
import sqlite3
from pathlib import Path
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
APP_NAME = os.getenv("APP_NAME", "Farmacias de Turno + Vademécum (MVP v2)")
ENV = os.getenv("ENV", "dev")
VADEMECUM_PATH = os.getenv("VADEMECUM_PATH", "./data/vademecum_clean.parquet")

# Initialize Enhanced database with LLM-enhanced commune matching
db = EnhancedPharmacyDatabase()

# Initialize Spanish AI Agent (will be done on startup)
spanish_agent = None

app = FastAPI(title=APP_NAME, version="0.2.0")

# Add cache middleware (temporarily disabled - sync/async compatibility)
# app.middleware("http")(CacheMiddleware(app))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include status router
app.include_router(status_router, prefix="/api")

# Mount static files for our modern frontend
app.mount("/templates/assets", StaticFiles(directory="templates/assets"), name="assets")

# Request/Response Models
class ChatPayload(BaseModel):
    message: str

class ChatSessionPayload(BaseModel):
    message: str
    session_id: Optional[str] = None

# Legacy constants (for backward compatibility)
DISCLAIMER = "Servicio informativo: no entregamos dosis, tratamientos ni diagnósticos. En urgencias, llama al 131."

REJECTION_TRIGGERS = [
    "dosis", "posología", "mg", "cada ", "frecuencia", "puedo mezclar",
    "interacción", "interacciones", "qué tomo", "que tomo", "diagnóstico", "diagnostico",
    "recetar", "recétame", "recetame", "para mi hijo", "embarazo"
]

@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection, Spanish AI Agent, database updates, and warm up cache"""
    global spanish_agent
    logger.info("🚀 Starting Pharmacy Finder application...")
    
    # Auto-update database if needed (check every startup)
    try:
        from app.services.data_updater import data_updater
        update_result = await data_updater.update_if_needed()
        if update_result.get('updated'):
            logger.info(f"✅ Database auto-updated: {update_result.get('pharmacy_count', 0)} pharmacies")
        else:
            logger.info(f"✅ Database is fresh: {update_result.get('pharmacy_count', 0)} pharmacies")
    except Exception as e:
        logger.warning(f"⚠️  Database auto-update failed: {e} - continuing with existing data")
    
    # Initialize Redis connection
    redis_client = await get_redis_client()
    connected = await redis_client.connect()
    
    if connected:
        logger.info("✅ Redis cache system initialized")
        
        # Initialize Spanish AI Agent
        try:
            spanish_agent = SpanishPharmacyAgent()
            logger.info("✅ Spanish AI Agent initialized and ready")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Spanish AI Agent: {e}")
            spanish_agent = None
        
        # Warm up cache with popular data
        try:
            await cache_warmup()
            logger.info("🔥 Cache warmup completed")
        except Exception as e:
            logger.error(f"⚠️  Cache warmup failed: {e}")
    else:
        logger.warning("⚠️  Redis unavailable - continuing with SQLite only")
    
    logger.info("🎯 Application startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up Redis connection"""
    logger.info("🛑 Shutting down Pharmacy Finder application...")
    
    redis_client = await get_redis_client()
    await redis_client.disconnect()
    
    logger.info("✅ Application shutdown completed")

@app.get("/admin/update-database")
async def force_database_update():
    """Force database update - admin endpoint"""
    try:
        from app.services.data_updater import data_updater
        result = await data_updater.force_update()
        
        if result.get('updated'):
            return {
                "success": True,
                "message": "Database updated successfully",
                "pharmacy_count": result.get('pharmacy_count', 0),
                "on_duty": result.get('on_duty', 0),
                "regular": result.get('regular', 0)
            }
        else:
            return {
                "success": False,
                "message": "Database update failed",
                "error": result.get('error', 'Unknown error')
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Update error: {str(e)}"
        }

@app.get("/admin/database-status")
async def get_database_status():
    """Get current database status - admin endpoint"""
    try:
        from app.services.data_updater import data_updater
        info = data_updater.get_database_age()
        return {
            "success": True,
            "database_info": info
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/health")
def health():
    return {"status": "ok", "env": ENV}

@app.get("/farmacias")
def farmacias(
    region: Optional[str] = Query(None),
    comuna: Optional[str] = Query(None),
    abierto: Optional[bool] = Query(False),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        items = get_locales_turno(region=region, comuna=comuna, abierto=abierto, limit=limit)
        if not items:
            items = get_locales(region=region, comuna=comuna, limit=limit)
        return {"items": items, "source": "MINSAL"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error consultando fuente oficial: {e}")

@app.get("/medicamentos")
def medicamentos(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
):
    items = load_vademecum(VADEMECUM_PATH)
    res = search_vademecum(items, q=q, limit=limit) if items else []
    return {"items": res, "source": "vademecum"}

# ======================================
# AI AGENT CHAT ENDPOINTS
# ======================================

@app.post("/chat")
async def chat_with_agent(payload: ChatSessionPayload):
    """
    Chat with the Spanish Pharmacy AI Agent
    Supports both session-based and stateless conversations
    """
    if not spanish_agent:
        raise HTTPException(status_code=503, detail="AI Agent not available")
    
    try:
        # Create new session if none provided
        if not payload.session_id:
            session_id = await spanish_agent.create_session()
        else:
            session_id = payload.session_id
        
        # Process message with the agent
        response = await spanish_agent.process_message(session_id, payload.message)
        
        if response.get("success"):
            return {
                "session_id": session_id,
                "reply": response.get("response", ""),
                "tools_used": response.get("tools_used", []),
                "tool_results": response.get("tool_results", []),  # Include tool results for frontend
                "response_time_ms": response.get("response_time_ms", 0),
                "model": response.get("model", "gpt-3.5-turbo")
            }
        else:
            return {
                "session_id": session_id,
                "reply": "Lo siento, hubo un error procesando tu mensaje. ¿Puedes intentar de nuevo?",
                "error": response.get("error"),
                "tools_used": [],
                "response_time_ms": 0
            }
            
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error en el chat: {str(e)}")

@app.post("/api/chat/session")
async def create_chat_session():
    """Create a new chat session with the AI agent"""
    if not spanish_agent:
        raise HTTPException(status_code=503, detail="AI Agent not available")
    
    try:
        session_id = await spanish_agent.create_session()
        return {
            "session_id": session_id,
            "status": "created",
            "message": "Nueva sesión de chat creada"
        }
    except Exception as e:
        logger.error(f"❌ Session creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Error creando sesión: {str(e)}")

@app.post("/api/chat/message")
async def send_chat_message(
    payload: ChatSessionPayload,
    session_id: Optional[str] = Query(None, description="Session ID for the conversation (also accepted in JSON body)")
):
    """Send a message to an existing chat session.
    Backward compatible: session_id can be provided either as query param or inside JSON payload
    to avoid 422/400 errors from clients sending it in the body.
    """
    if not spanish_agent:
        raise HTTPException(status_code=503, detail="AI Agent not available")

    # Prefer explicit query param, otherwise fall back to body
    effective_session_id = session_id or payload.session_id

    if not effective_session_id:
        raise HTTPException(status_code=400, detail="session_id is required (as query param or in JSON body)")

    try:
        response = await spanish_agent.process_message(effective_session_id, payload.message)
        return response
    except Exception as e:
        logger.error(f"❌ Message processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get conversation history for a session"""
    if not spanish_agent:
        raise HTTPException(status_code=503, detail="AI Agent not available")
    
    try:
        summary = await spanish_agent.get_session_summary(session_id)
        return summary
    except Exception as e:
        logger.error(f"❌ History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

@app.delete("/api/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session and its history"""
    if not spanish_agent:
        raise HTTPException(status_code=503, detail="AI Agent not available")
    
    try:
        success = await spanish_agent.delete_session(session_id)
        if success:
            return {"status": "deleted", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"❌ Session deletion error: {e}")
        raise HTTPException(status_code=500, detail=f"Error eliminando sesión: {str(e)}")

# ======================================
# LEGACY CHAT ENDPOINT (DEPRECATED)
# ======================================

@app.post("/chat/legacy")
def chat_legacy(payload: ChatPayload):
    """
    Legacy chat endpoint (deprecated - use /chat instead)
    Kept for backward compatibility
    """
    text = (payload.message or "").lower()

    if any(t in text for t in REJECTION_TRIGGERS):
        return {
            "reply": "No puedo entregar recomendaciones médicas (p. ej. dosis o diagnósticos). "
                     "Consulta con un profesional. En caso de urgencia, llama al 131.",
            "tool_used": None,
            "disclaimers": [DISCLAIMER]
        }

    if any(k in text for k in ["farmacia", "turno", "abierta", "abierto", "dirección", "direccion", "comuna", "región", "region"]):
        return {
            "reply": "Para buscar farmacias de turno usa `/farmacias?comuna=...&abierto=true` o indica región/comuna.",
            "tool_used": "SearchFarmaciasTool",
            "disclaimers": [DISCLAIMER]
        }

    if any(k in text for k in ["medicamento", "principio activo", "paracetamol", "ibuprofeno"]):
        return {
            "reply": "Para ver fichas informativas (no prescriptivas) usa `/medicamentos?q=...`.",
            "tool_used": "LookupMedicamentoTool",
            "disclaimers": [DISCLAIMER]
        }

    return {
        "reply": "Puedo ayudarte con farmacias de turno y fichas informativas de medicamentos. "
                 "Indica tu comuna o el nombre del medicamento. No entrego dosis ni diagnósticos.",
        "tool_used": None,
        "disclaimers": [DISCLAIMER]
    }

# New endpoints for the web interface
@app.get("/")
def read_root():
    """Serve the main web interface (modern version with AI chat)"""
    template_path = Path(__file__).parent.parent / "templates" / "index_modern.html"
    if template_path.exists():
        return FileResponse(template_path)
    return {"message": "Web interface not available. Use /docs for API documentation."}

@app.get("/legacy")
def read_legacy():
    """Serve the legacy web interface (original version)"""
    template_path = Path(__file__).parent.parent / "templates" / "index.html"
    if template_path.exists():
        return FileResponse(template_path)
    return {"message": "Legacy web interface not available. Use /docs for API documentation."}

@app.get("/modern")
def read_modern():
    """Redirect to main homepage (kept for compatibility)"""
    template_path = Path(__file__).parent.parent / "templates" / "index_modern.html"
    if template_path.exists():
        return FileResponse(template_path)
    return {"message": "Modern web interface not available. Use /docs for API documentation."}

@app.get("/templates/index_modern.html")
def serve_modern_template():
    """Direct access to modern template"""
    template_path = Path(__file__).parent.parent / "templates" / "index_modern.html"
    if template_path.exists():
        return FileResponse(template_path)

@app.get("/status")
def read_status():
    """Serve the system status dashboard"""
    template_path = Path(__file__).parent.parent / "templates" / "status.html"
    if template_path.exists():
        return FileResponse(template_path)
    return {"message": "Status dashboard not available."}
    return {"message": "Modern template not found"}

@app.get("/api/stats")
def get_stats():
    """Get database statistics"""
    try:
        from datetime import datetime
        stats = db.get_pharmacy_count()
        communes = db.get_all_communes()
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")

        return {
            "total": stats["total"],
            "turno": stats["turno"],
            "regular": stats["regular"],
            "communes": len(communes),
            "current_time": current_time,
            "current_date": current_date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {e}")

@app.get("/api/status")
async def get_system_status():
    """Get comprehensive system status for the status dashboard"""
    try:
        from datetime import datetime
        import sys
        import os
        
        # Get basic database stats
        stats = db.get_pharmacy_count()
        communes = db.get_all_communes()
        
        # Get data freshness information
        try:
            # Add tests directory to path and import DataQualityChecker
            tests_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests')
            sys.path.append(tests_path)
            from test_data_quality import DataQualityChecker
            
            checker = DataQualityChecker()
            freshness_results = checker.check_database_freshness()
            api_results = checker.check_api_availability()
            
            # Determine data freshness status
            days_since_update = freshness_results.get('days_since_update', 0)
            if isinstance(days_since_update, int):
                if days_since_update <= 1:
                    data_status = "healthy"
                    data_message = "Data is current"
                elif days_since_update <= 3:
                    data_status = "warning"
                    data_message = "Data is slightly stale"
                else:
                    data_status = "error"
                    data_message = "Data needs updating"
            else:
                data_status = "warning"
                data_message = "Unable to determine data age"
                
        except Exception as e:
            logger.warning(f"Could not get data quality info: {e}")
            freshness_results = {}
            api_results = {}
            data_status = "warning"
            data_message = "Data quality check unavailable"
        
        # Get Redis cache status
        try:
            from app.middleware.cache_middleware import cache_health_check
            redis_health = await cache_health_check()
            redis_status = "healthy" if redis_health.get("redis_available", False) else "error"
            redis_message = "Connected and operational" if redis_status == "healthy" else "Not available"
        except Exception as e:
            redis_status = "error"
            redis_message = f"Cache unavailable: {str(e)}"
            redis_health = {}
        
        # Calculate coordinate coverage
        try:
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM pharmacies WHERE lat IS NOT NULL AND lng IS NOT NULL')
                with_coords = cursor.fetchone()[0]
                coordinate_coverage = (with_coords / stats["total"]) * 100 if stats["total"] > 0 else 0
        except Exception:
            coordinate_coverage = 0
        
        # System information
        current_time = datetime.now()
        
        return {
            "status": "healthy",  # Overall system status
            "timestamp": current_time.isoformat(),
            "components": {
                "database": {
                    "status": data_status,
                    "message": data_message,
                    "statistics": {
                        "total_pharmacies": stats["total"],
                        "turno_pharmacies": stats["turno"],
                        "regular_pharmacies": stats["regular"],
                        "total_communes": len(communes),
                        "coordinate_coverage": round(coordinate_coverage, 1)
                    },
                    "freshness": {
                        "latest_update": freshness_results.get('latest_update', 'Unknown'),
                        "days_since_update": freshness_results.get('days_since_update', 'Unknown'),
                        "hours_since_update": freshness_results.get('hours_since_update', 'Unknown'),
                        "db_file_modified": freshness_results.get('db_file_modified', 'Unknown')
                    }
                },
                "redis": {
                    "status": redis_status,
                    "message": redis_message,
                    "statistics": redis_health
                },
                "system": {
                    "status": "healthy",
                    "message": "System operational",
                    "statistics": {
                        "current_time": current_time.strftime("%H:%M:%S"),
                        "current_date": current_time.strftime("%Y-%m-%d"),
                        "server_uptime": "Running"
                    }
                },
                "api_endpoints": {
                    "status": "healthy" if api_results else "warning",
                    "message": "MINSAL API endpoints monitored",
                    "endpoints": api_results
                }
            },
            "actions": {
                "update_data": "/api/data/update",
                "check_freshness": "/api/data/freshness",
                "invalidate_cache": "/api/cache/invalidate",
                "cache_stats": "/api/cache/stats"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ System status check error: {e}")
        raise HTTPException(status_code=500, detail=f"System status error: {e}")

@app.get("/api/open-now")
def get_open_now_pharmacies(
    lat: Optional[float] = Query(None, description="Latitude for location-based search"),
    lng: Optional[float] = Query(None, description="Longitude for location-based search"),
    comuna: Optional[str] = Query(None, description="Commune for commune-based search"),
    radius: float = Query(5.0, description="Search radius in km")
):
    """Get pharmacies that are currently open"""
    try:
        if lat is not None and lng is not None:
            pharmacies = db.find_nearby_pharmacies_open_now(lat, lng, radius)
        elif comuna:
            pharmacies = db.find_by_comuna_open_now(comuna)
        else:
            # Get all pharmacies and filter by current time
            # This is less efficient but works as fallback
            all_pharmacies = []
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM pharmacies LIMIT 1000')  # Limit for performance
                rows = cursor.fetchall()
                all_pharmacies = [db._row_to_pharmacy(row) for row in rows]

            pharmacies = [p for p in all_pharmacies if db.is_pharmacy_currently_open(p)]

        return {
            "items": [
                {
                    "local_id": p.local_id,
                    "nombre": p.nombre,
                    "direccion": p.direccion,
                    "comuna": p.comuna,
                    "localidad": p.localidad,
                    "telefono": p.telefono,
                    "lat": p.lat,
                    "lng": p.lng,
                    "hora_apertura": p.hora_apertura,
                    "hora_cierre": p.hora_cierre,
                    "dia_funcionamiento": p.dia_funcionamiento,
                    "es_turno": p.es_turno,
                    "abierto_ahora": True
                }
                for p in pharmacies[:50]  # Limit results
            ],
            "count": len(pharmacies),
            "source": "database"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding open pharmacies: {e}")

@app.get("/api/nearby")
def get_nearby_pharmacies(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: float = Query(5.0, description="Search radius in km"),
    abierto: bool = Query(False, description="Only open pharmacies"),
    abierto_ahora: bool = Query(False, description="Only pharmacies open right now")
):
    """Find pharmacies near a location you can change the radius if needed"""
    try:
        if abierto_ahora:
            # Use new method that checks current time
            pharmacies = db.find_nearby_pharmacies_open_now(lat, lng, radius)
        else:
            pharmacies = db.find_nearby_pharmacies(lat, lng, radius, abierto)

        return {
            "items": [
                {
                    "local_id": p.local_id,
                    "nombre": p.nombre,
                    "direccion": p.direccion,
                    "comuna": p.comuna,
                    "localidad": p.localidad,
                    "telefono": p.telefono,
                    "lat": p.lat,
                    "lng": p.lng,
                    "hora_apertura": p.hora_apertura,
                    "hora_cierre": p.hora_cierre,
                    "dia_funcionamiento": p.dia_funcionamiento,
                    "es_turno": p.es_turno,
                    "abierto_ahora": db.is_pharmacy_currently_open(p)
                }
                for p in pharmacies
            ],
            "source": "database"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding nearby pharmacies: {e}")

@app.get("/api/communes")
def get_communes():
    """Get list of all communes"""
    try:
        communes = db.get_all_communes()
        return {"communes": communes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting communes: {e}")

@app.get("/api/search")
def search_pharmacies(
    comuna: Optional[str] = Query(None, description="Commune name to search in"),
    abierto: bool = Query(False, description="Only show pharmacies de turno"),
    limit: int = Query(50, description="Maximum number of results")
):
    """Search pharmacies by commune"""
    try:
        if comuna:
            pharmacies = db.find_by_comuna(comuna, only_open=abierto)
        else:
            # Return some default pharmacies
            pharmacies = []
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                if abierto:
                    cursor.execute('SELECT * FROM pharmacies WHERE es_turno = 1 LIMIT ?', (limit,))
                else:
                    cursor.execute('SELECT * FROM pharmacies LIMIT ?', (limit,))
                rows = cursor.fetchall()
                pharmacies = [db._row_to_pharmacy(row) for row in rows]

        return {
            "items": [
                {
                    "local_id": p.local_id,
                    "nombre": p.nombre,
                    "direccion": p.direccion,
                    "comuna": p.comuna,
                    "localidad": p.localidad,
                    "telefono": p.telefono,
                    "lat": p.lat,
                    "lng": p.lng,
                    "hora_apertura": p.hora_apertura,
                    "hora_cierre": p.hora_cierre,
                    "dia_funcionamiento": p.dia_funcionamiento,
                    "es_turno": p.es_turno,
                    "abierto_ahora": db.is_pharmacy_currently_open(p)
                }
                for p in pharmacies[:limit]
            ],
            "count": len(pharmacies),
            "source": "database"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching pharmacies: {e}")

# =============================================================================
# CACHE MANAGEMENT ENDPOINTS
# =============================================================================

@app.get("/api/cache/health")
async def get_cache_health():
    """Get cache system health status"""
    try:
        health_info = await cache_health_check()
        return {
            "status": "ok" if health_info.get("operations_healthy", False) else "degraded",
            "cache_system": health_info,
            "timestamp": health_info.get("timestamp")
        }
    except Exception as e:
        logger.error(f"❌ Cache health check error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "cache_system": {"status": "error"}
        }

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get detailed cache statistics"""
    try:
        redis_client = await get_redis_client()
        stats = redis_client.get_cache_stats()
        
        return {
            "redis_stats": stats,
            "cache_config": {
                "ttl_critical": redis_client.ttl_critical,
                "ttl_high": redis_client.ttl_high,
                "ttl_medium": redis_client.ttl_medium,
                "ttl_low": redis_client.ttl_low,
                "fallback_enabled": redis_client.fallback_enabled,
                "max_stale_age": redis_client.max_stale_age
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Cache stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Cache stats error: {e}")

@app.post("/api/cache/invalidate")
async def invalidate_cache():
    """Manually invalidate all pharmacy cache entries"""
    try:
        result = await manual_cache_invalidation()
        
        if result["status"] == "manual_invalidation_completed":
            return {
                "status": "success",
                "message": f"Invalidated {result['invalidated']} cache entries",
                "invalidated_count": result["invalidated"],
                "timestamp": result["timestamp"]
            }
        else:
            return {
                "status": "error",
                "message": result.get("message", "Unknown error"),
                "timestamp": result.get("timestamp")
            }
    except Exception as e:
        logger.error(f"❌ Manual cache invalidation error: {e}")
        raise HTTPException(status_code=500, detail=f"Cache invalidation error: {e}")

@app.get("/api/cache/invalidation-check")
async def run_invalidation_check():
    """Run cache invalidation check and report results"""
    try:
        invalidation_manager = await get_invalidation_manager()
        result = await invalidation_manager.run_invalidation_check()
        
        return {
            "status": result["status"],
            "result": result,
            "timestamp": result.get("timestamp", asyncio.get_event_loop().time())
        }
    except Exception as e:
        logger.error(f"❌ Invalidation check error: {e}")
        raise HTTPException(status_code=500, detail=f"Invalidation check error: {e}")

@app.post("/api/cache/warmup")
async def warm_cache():
    """Manually trigger cache warmup"""
    try:
        await cache_warmup()
        return {
            "status": "success",
            "message": "Cache warmup completed",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"❌ Cache warmup error: {e}")
        raise HTTPException(status_code=500, detail=f"Cache warmup error: {e}")

@app.get("/api/data/freshness")
async def check_data_freshness():
    """Check database data freshness and update status"""
    try:
        # Import required modules
        import sys
        import os
        import sqlite3
        from datetime import datetime
        
        # Add tests directory to path and import DataQualityChecker
        tests_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests')
        sys.path.append(tests_path)
        from test_data_quality import DataQualityChecker
        
        checker = DataQualityChecker()
        
        # Get API status
        api_results = checker.check_api_availability()
        
        # Get database freshness
        freshness_results = checker.check_database_freshness()
        
        # Get basic stats
        stats = db.get_pharmacy_count()
        
        # Determine overall status
        days_since_update = freshness_results.get('days_since_update', 0)
        api_ok = all("✅" in result['status'] for result in api_results.values())
        
        if isinstance(days_since_update, int):
            if days_since_update <= 1:
                overall_status = "fresh"
                status_icon = "✅"
                recommendation = "Data is current"
            elif days_since_update <= 3:
                overall_status = "stale"
                status_icon = "⚠️"
                recommendation = "Consider updating data soon"
            else:
                overall_status = "very_old"
                status_icon = "❌"
                recommendation = "Data update recommended immediately"
        else:
            overall_status = "unknown"
            status_icon = "❓"
            recommendation = "Unable to determine data age"
        
        return {
            "status": "success",
            "data_freshness": {
                "overall_status": overall_status,
                "status_icon": status_icon,
                "recommendation": recommendation,
                "latest_update": freshness_results.get('latest_update'),
                "days_since_update": days_since_update,
                "hours_since_update": freshness_results.get('hours_since_update'),
                "db_file_modified": freshness_results.get('db_file_modified'),
                "freshness_status": freshness_results.get('freshness_status')
            },
            "api_status": {
                "overall_ok": api_ok,
                "endpoints": api_results
            },
            "database_stats": {
                "total_pharmacies": stats['total'],
                "turno_pharmacies": stats['turno'],
                "regular_pharmacies": stats['regular']
            },
            "timestamp": datetime.now().isoformat(),
            "update_commands": {
                "manual_update": "python data/import_data.py",
                "quick_check": "python tests/quick_check.py",
                "full_quality_check": "python tests/test_data_quality.py"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Data freshness check error: {e}")
        raise HTTPException(status_code=500, detail=f"Data freshness check error: {e}")

@app.post("/api/data/update")
async def trigger_data_update():
    """Trigger a manual data update from MINSAL API"""
    try:
        import subprocess
        import sys
        import os
        
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Run the import script
        result = subprocess.run(
            [sys.executable, os.path.join(project_root, "data", "import_data.py")],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            # If successful, invalidate cache
            invalidation_manager = get_invalidation_manager()
            await manual_cache_invalidation()
            
            return {
                "status": "success",
                "message": "Data update completed successfully",
                "output": result.stdout,
                "timestamp": datetime.now().isoformat(),
                "next_steps": "Cache has been invalidated. Fresh data is now available."
            }
        else:
            return {
                "status": "error", 
                "message": "Data update failed",
                "error_output": result.stderr,
                "return_code": result.returncode,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Data update error: {e}")
        raise HTTPException(status_code=500, detail=f"Data update error: {e}")


# 🔍 TEMPORARY TESTING ENDPOINT FOR CLICKABLE LINKS
@app.get("/test-links")
async def test_links():
    """Endpoint temporal para probar enlaces clickeables directamente"""
    from fastapi.responses import HTMLResponse
    
    test_html = r"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔍 Test de Enlaces Clickeables</title>
        <link rel="stylesheet" href="/templates/assets/css/main.css">
        <style>
            body { padding: 40px; font-family: Arial, sans-serif; background: #f5f5f5; }
            .test-section { background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .test-title { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        </style>
    </head>
    <body>
        <h1>🔍 Test de Enlaces Clickeables - Diagnóstico</h1>
        
        <div class="test-section">
            <h3 class="test-title">Test 1: Enlaces Directos (Sin JavaScript)</h3>
            <p>Estos enlaces deberían funcionar inmediatamente:</p>
            <a href="https://maps.google.com/maps?q=-33.4489,-70.6693" target="_blank" class="pharmacy-link">📍 Google Maps Directo</a><br><br>
            <a href="tel:+56987654321" class="phone-link">📞 Llamar Test</a><br><br>
        </div>
        
        <div class="test-section">
            <h3 class="test-title">Test 2: Estructura AI Response</h3>
            <p>Simulando respuesta del AI con nueva estructura:</p>
            <div class="message-content-main">
                <div class="ai-response-content">
                    <div class="pharmacy-name">🏪 FARMACIA TEST</div>
                    <div class="pharmacy-address">📍 Dirección Test 123</div>
                    <div class="pharmacy-phone">📞 +56 9 8765 4321</div>
                    <div class="pharmacy-hours">⏰ Lunes 08:00 - 18:00</div>
                    <a href="https://maps.google.com/maps?q=-33.4489,-70.6693" target="_blank" class="pharmacy-link">🗺️ Ver en Maps</a>
                </div>
            </div>
        </div>
        
        <div class="test-section">
            <h3 class="test-title">Test 3: JavaScript Conversion</h3>
            <p>Contenido que será procesado por JavaScript:</p>
            <div id="js-test-content">
                🏪 FARMACIA JAVASCRIPT<br>
                📍 Dirección: Test JS 456<br>
                📞 Teléfono: +56 9 1111 2222<br>
                ⏰ Horario: Martes 09:00 - 19:00<br>
                🌐 [Ver en Google Maps](https://maps.google.com/maps?q=-33.4489,-70.6693)<br>
            </div>
        </div>
        
        <div class="test-section">
            <h3 class="test-title">Test 4: Console Debug</h3>
            <p>Abre la consola del navegador (F12) y pega este código:</p>
            <textarea readonly style="width: 100%; height: 150px; font-family: monospace;">
// Test de formatAIResponse
const testInput = "🏪 FARMACIA CONSOLE\\n📞 Teléfono: +56 9 3333 4444\\n🌐 [Ver en Google Maps](https://maps.google.com/maps?q=-33.4489,-70.6693)";
const testDiv = document.getElementById('js-test-content');
if (window.chatManager && window.chatManager.formatAIResponse) {
    const formatted = window.chatManager.formatAIResponse(testInput);
    console.log('Formatted result:', formatted);
    testDiv.innerHTML = formatted;
} else {
    console.log('ChatManager not available');
}
            </textarea>
        </div>
        
        <script src="/templates/assets/js/chat.js" type="module"></script>
        <div class="test-section">
            <h3 class="test-title">Test 5: Diagnóstico Automático (sin consola)</h3>
            <p>Resultados del diagnóstico aparecerán abajo; si hay overlays que bloquean clicks, usa el botón para deshabilitarlos temporalmente.</p>
            <button id="disable-overlays" style="padding:8px 12px;border-radius:6px;border:none;background:#f44336;color:#fff;cursor:pointer;margin-bottom:8px;">Deshabilitar overlays (temporal)</button>
            <div id="diagnostic-output" style="background:#fafafa;padding:12px;border-radius:8px;border:1px solid #eee;max-height:320px;overflow:auto;"></div>
        </div>
        <script>
            // Local copy of the formatter (mirrors chat.js::formatAIResponse) so this page doesn't require the ChatManager instance.
            function localFormatAIResponse(content) {
                let formatted = content
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');
                formatted = formatted.replace(/\\n/g, '<br>');
                formatted = formatted.replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" target="_blank" class="pharmacy-link">$1</a>');
                formatted = formatted.replace(/\\b(tel:\\+\\d+[0-9\\-\\s]*)/g, '<a href="$1" class="phone-link">📞 Llamar</a>');
                formatted = formatted.replace(/🌐\\s*<a([^>]*href[^>]*maps[^>]*)>([^<]*)<\\/a>/gi, '<span class="map-link">🗺️ <a$1><strong>$2</strong></a></span>');
                formatted = formatted.replace(/🏪\\s*([^📍\\n<]+)/g, '<div class="pharmacy-name">🏪 <strong>$1</strong></div>');
                formatted = formatted.replace(/📍\\s*([^<\\n⏰📞🌐]+)/g, '<div class="pharmacy-address">📍 <em>$1</em></div>');
                formatted = formatted.replace(/📞\\s*([^<\\n⏰📍🌐]+)/g, '<div class="pharmacy-phone">📞 $1</div>');
                formatted = formatted.replace(/⏰\\s*([^<\\n📍📞🌐]+)/g, '<div class="pharmacy-hours">⏰ $1</div>');
                formatted = formatted.replace(/�([^<\\n]*)/g, '<span class="emergency-indicator">�$1</span>');
                return formatted;
            }

            function runDiagnostic() {
                const out = document.getElementById('diagnostic-output');
                out.innerHTML = '';
                const testInput = `🏪 FARMACIA CONSOLE\n📞 Teléfono: tel:+56933334444\n🌐 [Ver en Google Maps](https://maps.google.com/maps?q=-33.4489,-70.6693)`;
                const formatted = localFormatAIResponse(testInput);
                // Render formatted into a preview box
                const preview = document.createElement('div');
                preview.style.padding = '8px';
                preview.style.border = '1px dashed #ddd';
                preview.style.marginBottom = '8px';
                preview.innerHTML = '<strong>Preview HTML:</strong><br>' + formatted;
                out.appendChild(preview);

                // Append anchor summary
                const temp = document.createElement('div');
                temp.innerHTML = formatted;
                const anchors = temp.querySelectorAll('a');
                const report = document.createElement('div');
                report.innerHTML = `<strong>Anchors found:</strong> ${anchors.length}`;
                out.appendChild(report);

                anchors.forEach((a, i) => {
                    const info = document.createElement('div');
                    const rect = a.getBoundingClientRect();
                    info.textContent = `${i}: href=${a.href} text="${a.textContent.trim()}"`;
                    out.appendChild(info);
                });

                // ElementFromPoint check (attempt at viewport center for each link)
                const efp = document.createElement('div');
                efp.innerHTML = '<strong>elementFromPoint checks:</strong>';
                out.appendChild(efp);
                anchors.forEach((a, i) => {
                    // Insert preview anchor into DOM so elementFromPoint can resolve
                    const anchorWrap = document.createElement('div');
                    anchorWrap.style.position = 'relative';
                    anchorWrap.style.margin = '6px 0';
                    anchorWrap.innerHTML = a.outerHTML;
                    out.appendChild(anchorWrap);
                    // Wait a tick to allow layout
                    const r = anchorWrap.querySelector('a').getBoundingClientRect();
                    const el = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
                    const elInfo = document.createElement('div');
                    elInfo.textContent = `anchor ${i} elementFromPoint => ${el ? (el.tagName + (el.className ? ' .' + el.className : '')) : 'null'}`;
                    out.appendChild(elInfo);
                });

                // List potential overlays
                const overlays = document.querySelectorAll('.loading-overlay, .card-overlay, .overlay, .modal-backdrop');
                const ov = document.createElement('div');
                ov.innerHTML = `<strong>Potential overlays found:</strong> ${overlays.length}`;
                out.appendChild(ov);
                overlays.forEach(o => {
                    const i = document.createElement('div');
                    const s = getComputedStyle(o);
                    i.textContent = `overlay ${o.className} display=${s.display} pointerEvents=${s.pointerEvents} zIndex=${s.zIndex}`;
                    out.appendChild(i);
                });
            }

            document.addEventListener('DOMContentLoaded', () => {
                runDiagnostic();
                const btn = document.getElementById('disable-overlays');
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.loading-overlay, .card-overlay, .overlay, .modal-backdrop').forEach(o => {
                        o.style.pointerEvents = 'none';
                        o.style.display = 'none';
                    });
                    runDiagnostic();
                });
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(test_html)


# 🔍 SIMPLE CHAT TEST ENDPOINT  
@app.post("/api/chat")
async def simple_chat_test(request: ChatPayload):
    """Endpoint simplificado para test de chat"""
    message = request.message
    
    # Respuesta de prueba con enlaces markdown
    test_response = f"""Encontré 3 farmacias de turno en Maipú:

1. 🏪 FARMAQUINTA
📍 Dirección: AVENIDA VALPARAISO 1621, VILLA ALEMANA
📞 Teléfono: +56 79 859 135
⏰ Horario: Viernes 00:00 - 23:59
🌐 [Ver en Google Maps](https://maps.google.com/maps?q=-33.0449112,-71.3856936)

2. 🏪 BELLFARMA  
📍 Dirección: HUANHUALI 1331, VILLA ALEMANA
📞 Teléfono: +563118844
⏰ Horario: Sábado 09:00 - 18:00 (Por abrir)
🌐 [Ver en Google Maps](https://maps.google.com/maps?q=-33.058657929509,-71.3860337445243)

3. 🏪 FARMA CHILE
📍 Dirección: JORGE DÉLANO N° 70, MAIPU
📞 Teléfono: +56
⏰ Horario: Sábado 08:00 - 07:59 (Por abrir)  
🌐 [Ver en Google Maps](https://maps.google.com/maps?q=-33.482677,-70.747523)"""
    
    return {"message": test_response}

@app.get("/vademecum-explorer")
async def vademecum_explorer():
    """Interactive table to explore vademecum data"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📊 Explorador de Vademécum</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .header { text-align: center; margin-bottom: 30px; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .controls { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; align-items: center; }
            .search-box { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; min-width: 200px; }
            .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-weight: 500; }
            .btn-primary { background: #007bff; color: white; }
            .btn:hover { opacity: 0.8; }
            .table-container { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; min-width: 800px; }
            th { background: #f8f9fa; padding: 12px 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6; cursor: pointer; white-space: nowrap; }
            th:hover { background: #e9ecef; }
            td { padding: 10px 8px; border-bottom: 1px solid #dee2e6; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            tr:nth-child(even) { background: #f8f9fa; }
            tr:hover { background: #e3f2fd !important; }
            .loading { text-align: center; padding: 40px; color: #666; }
            .status { margin: 10px 0; padding: 10px; border-radius: 4px; background: #f8f9fa; border-left: 4px solid #007bff; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Explorador de Vademécum</h1>
            <p>Base de datos de medicamentos</p>
        </div>
        
        <div class="controls">
            <input type="text" class="search-box" id="searchBox" placeholder="Buscar medicamentos (mín 2 caracteres)...">
            <button class="btn btn-primary" onclick="searchMedicines()">🔍 Buscar</button>
        </div>
        
        <div class="status" id="status">
            Escribe al menos 2 caracteres para buscar medicamentos...
        </div>
        
        <div class="table-container">
            <div class="loading" id="loading" style="display: none;">Cargando datos...</div>
            <table id="dataTable" style="display: none;">
                <thead id="tableHead"></thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>
        
        <script>
            async function searchMedicines() {
                const searchTerm = document.getElementById('searchBox').value.trim();
                
                if (searchTerm.length < 2) {
                    document.getElementById('status').innerHTML = 'Escribe al menos 2 caracteres para buscar.';
                    return;
                }
                
                try {
                    document.getElementById('loading').style.display = 'block';
                    document.getElementById('dataTable').style.display = 'none';
                    document.getElementById('status').innerHTML = 'Buscando...';
                    
                    const response = await fetch(`/medicamentos?q=${encodeURIComponent(searchTerm)}&limit=50`);
                    const data = await response.json();
                    
                    if (data.items && data.items.length > 0) {
                        displayData(data.items);
                        document.getElementById('status').innerHTML = `Encontrados ${data.items.length} medicamentos`;
                    } else {
                        document.getElementById('status').innerHTML = 'No se encontraron medicamentos.';
                        document.getElementById('dataTable').style.display = 'none';
                    }
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById('status').innerHTML = 'Error al buscar: ' + error.message;
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            }
            
            function displayData(items) {
                if (items.length === 0) return;
                
                const headers = Object.keys(items[0]);
                const tableHead = document.getElementById('tableHead');
                tableHead.innerHTML = '<tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
                
                const tableBody = document.getElementById('tableBody');
                tableBody.innerHTML = items.map(row => 
                    '<tr>' + 
                    headers.map(header => {
                        const cellValue = row[header] || '';
                        const displayValue = cellValue.toString().length > 50 ? 
                            cellValue.toString().substring(0, 50) + '...' : 
                            cellValue;
                        return `<td title="${cellValue}">${displayValue}</td>`;
                    }).join('') + 
                    '</tr>'
                ).join('');
                
                document.getElementById('dataTable').style.display = 'table';
            }
            
            document.getElementById('searchBox').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') searchMedicines();
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)
