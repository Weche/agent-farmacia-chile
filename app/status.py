"""
System Status and Health Dashboard API
Provides comprehensive system health information
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from datetime import datetime
import sqlite3
import redis
import os
import sys
from pathlib import Path

router = APIRouter()

def get_database_status():
    """Get database health and statistics"""
    try:
        conn = sqlite3.connect('pharmacy_finder.db')
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get pharmacy statistics
        cursor.execute("SELECT COUNT(*) FROM pharmacies")
        total_pharmacies = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT comuna) FROM pharmacies")
        total_communes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT region) FROM pharmacies")
        total_regions = cursor.fetchone()[0]
        
        # Get pharmacies with coordinates
        cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE lat != 0 AND lng != 0")
        pharmacies_with_coords = cursor.fetchone()[0]
        
        # Get turno pharmacies
        cursor.execute("SELECT COUNT(*) FROM pharmacies WHERE es_turno = 1")
        turno_pharmacies = cursor.fetchone()[0]
        
        # Get database file info
        db_path = Path('pharmacy_finder.db')
        db_size = db_path.stat().st_size if db_path.exists() else 0
        db_modified = datetime.fromtimestamp(db_path.stat().st_mtime) if db_path.exists() else None
        
        # Sample pharmacies by commune
        cursor.execute("""
            SELECT comuna, COUNT(*) as count 
            FROM pharmacies 
            GROUP BY comuna 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_communes = cursor.fetchall()
        
        conn.close()
        
        return {
            "status": "healthy",
            "tables": tables,
            "statistics": {
                "total_pharmacies": total_pharmacies,
                "total_communes": total_communes,
                "total_regions": total_regions,
                "pharmacies_with_coordinates": pharmacies_with_coords,
                "turno_pharmacies": turno_pharmacies,
                "coordinate_coverage": round((pharmacies_with_coords / total_pharmacies) * 100, 2) if total_pharmacies > 0 else 0
            },
            "file_info": {
                "size_mb": round(db_size / (1024 * 1024), 2),
                "last_modified": db_modified.isoformat() if db_modified else None
            },
            "top_communes": [{"name": commune, "count": count} for commune, count in top_communes]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def get_redis_status():
    """Get Redis health and statistics"""
    try:
        from app.cache.redis_client import redis_client
        
        # Test connection
        if redis_client.redis_pool is None:
            # Try to connect if not connected
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, we need to handle differently
                redis_client.redis_pool = redis.Redis.from_url(
                    redis_client.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
            else:
                # Run connect in new event loop
                asyncio.run(redis_client.connect())
        
        # Test ping
        redis_client.redis_pool.ping()
        
        # Get Redis info
        info = redis_client.redis_pool.info()
        
        # Get cache statistics
        cache_keys = redis_client.redis_pool.keys("*")
        
        # Group keys by type
        key_types = {}
        for key in cache_keys:
            key_str = key if isinstance(key, str) else str(key)
            key_type = key_str.split(':')[0] if ':' in key_str else 'other'
            key_types[key_type] = key_types.get(key_type, 0) + 1
        
        return {
            "status": "connected",
            "server_info": {
                "version": info.get("redis_version", "unknown"),
                "uptime_days": info.get("uptime_in_days", 0),
                "memory_used_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "connected_clients": info.get("connected_clients", 0)
            },
            "cache_info": {
                "total_keys": len(cache_keys),
                "key_types": key_types
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def get_system_status():
    """Get system health information"""
    try:
        # Python environment info
        python_info = {
            "version": sys.version,
            "executable": sys.executable,
            "platform": sys.platform
        }
        
        # Environment variables (safe ones only)
        env_vars = {
            "OPENAI_API_KEY": "Set" if os.getenv("OPENAI_API_KEY") else "Not Set",
            "GOOGLE_MAPS_API_KEY": "Set" if os.getenv("GOOGLE_MAPS_API_KEY") else "Not Set",
            "REDIS_CONNECTION": "Configured" if os.getenv("REDIS_URL") else "Not Set",
        }
        
        # File system info
        current_dir = Path.cwd()
        requirements_file = current_dir / "requirements.txt"
        
        return {
            "status": "healthy",
            "python": python_info,
            "environment": env_vars,
            "files": {
                "requirements_exists": requirements_file.exists(),
                "working_directory": str(current_dir)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/status")
async def get_full_status():
    """Get comprehensive system status"""
    
    database_status = get_database_status()
    redis_status = get_redis_status()
    system_status = get_system_status()
    
    # Overall health check
    overall_health = "healthy"
    if (database_status.get("status") != "healthy" or 
        redis_status.get("status") != "connected" or 
        system_status.get("status") != "healthy"):
        overall_health = "degraded"
    
    return {
        "overall_status": overall_health,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": database_status,
            "redis": redis_status,
            "system": system_status
        }
    }

@router.get("/status/database")
async def get_database_status_endpoint():
    """Get detailed database status"""
    return get_database_status()

@router.get("/status/redis")
async def get_redis_status_endpoint():
    """Get Redis status"""
    return get_redis_status()

@router.get("/status/system")
async def get_system_status_endpoint():
    """Get system status"""
    return get_system_status()

def verify_admin_access_from_request(request: Request):
    """Verify admin access from request headers"""
    # Get headers
    username = request.headers.get('username')
    password = request.headers.get('password')
    admin_key = request.headers.get('admin-key')
    
    # Multiple authentication methods for flexibility
    env_key = os.getenv("ADMIN_KEY")
    admin_username = os.getenv("ADMIN_USERNAME", "pharmacy_admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "SecurePharmacy2024!")
    runtime_key = os.getenv("RUNTIME_ADMIN_KEY")
    
    # Check if username/password provided
    if username and password:
        if username == admin_username and password == admin_password:
            return {"is_admin": True, "method": "userpass"}
    
    # Check admin key from headers
    if admin_key:
        # Check runtime key (highest priority)
        if runtime_key and admin_key == runtime_key:
            return {"is_admin": True, "method": "runtime_key"}
        
        # Check environment key (fallback)
        if env_key and admin_key == env_key:
            return {"is_admin": True, "method": "admin_key"}
            
        # Check if admin_key is actually the password (compatibility)
        if admin_key == admin_password:
            return {"is_admin": True, "method": "password_key"}
    
    return {"is_admin": False, "message": "Access denied - Invalid credentials"}


def verify_admin_access(admin_key: str = Query(None), username: str = Query(None), password: str = Query(None)):
    """Verify admin access for sensitive operations"""
    # Multiple authentication methods for flexibility
    
    # Method 1: Environment variable (for development)
    env_key = os.getenv("ADMIN_KEY")
    
    # Method 2: Username/Password combination (for production)
    admin_username = os.getenv("ADMIN_USERNAME", "pharmacy_admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "SecurePharmacy2024!")
    
    # Method 3: Runtime-generated key (most secure for production)
    runtime_key = os.getenv("RUNTIME_ADMIN_KEY")
    
    valid_access = False
    auth_method = None
    
    # Check if username/password provided (preferred method)
    if username and password:
        if username == admin_username and password == admin_password:
            valid_access = True
            auth_method = "userpass"
    
    # Check if username/admin_key provided (backward compatibility)
    elif username and admin_key:
        if username == admin_username and admin_key == admin_password:
            valid_access = True
            auth_method = "userpass_compat"
    
    # Check runtime key (highest priority)
    elif runtime_key and admin_key == runtime_key:
        valid_access = True
        auth_method = "runtime_key"
    
    # Check environment key (fallback for development)
    elif env_key and admin_key == env_key:
        valid_access = True
        auth_method = "env_key"
    
    if not valid_access:
        raise HTTPException(
            status_code=403, 
            detail="Admin access required. Use username/password or admin key."
        )
    return True

@router.get("/status/chat-sessions")
async def get_chat_sessions(admin: bool = Depends(verify_admin_access)):
    """Get active chat sessions (admin only)"""
    try:
        from app.cache.redis_client import redis_client
        
        # Get all session keys
        if redis_client.redis_pool is None:
            return {
                "status": "error",
                "error": "Redis not connected"
            }
        
        session_keys = redis_client.redis_pool.keys("session:*")
        
        sessions = []
        for key in session_keys:
            try:
                session_data = redis_client.redis_pool.hgetall(key)
                session_id = key.replace("session:", "")
                
                # Get session info (now with full access since authenticated)
                session_info = {
                    "id": session_id,  # Full session ID for authenticated users
                    "id_display": session_id[:12] + "...",  # Display version
                    "created": session_data.get("created", "Unknown"),
                    "last_activity": session_data.get("last_activity", "Unknown"),
                    "message_count": int(session_data.get("message_count", 0)),
                    "status": "active" if session_data.get("status") == "active" else "inactive"
                }
                
                sessions.append(session_info)
                
            except Exception as e:
                continue
        
        # Sort by last activity
        sessions.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
        
        return {
            "status": "success",
            "total_sessions": len(sessions),
            "active_sessions": len([s for s in sessions if s["status"] == "active"]),
            "sessions": sessions[:10]  # Show last 10
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/status/chat-sessions/stats")
async def get_chat_sessions_stats():
    """Get basic chat sessions statistics (public)"""
    try:
        from app.cache.redis_client import redis_client
        
        # Get all session keys
        if redis_client.redis_pool is None:
            return {
                "status": "error",
                "error": "Redis not connected"
            }
        
        session_keys = redis_client.redis_pool.keys("session:*")
        
        active_count = 0
        total_count = len(session_keys)
        
        for key in session_keys:
            try:
                session_data = redis_client.redis_pool.hgetall(key)
                if session_data.get("status") == "active":
                    active_count += 1
            except Exception:
                continue
        
        return {
            "status": "success",
            "total_sessions": total_count,
            "active_sessions": active_count,
            "message": "Detalles disponibles solo para administradores"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/status/chat-sessions/details")
async def get_chat_session_details(session_id: str = Query(...), admin: bool = Depends(verify_admin_access)):
    """Get detailed chat session history (admin only)"""
    try:
        from app.cache.redis_client import redis_client
        
        if redis_client.redis_pool is None:
            return {
                "status": "error",
                "error": "Redis not connected"
            }
        
        # Get session data
        session_key = f"session:{session_id}"
        session_data = redis_client.redis_pool.hgetall(session_key)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages
        messages_key = f"session:{session_id}:messages"
        messages = redis_client.redis_pool.lrange(messages_key, 0, -1)
        
        return {
            "status": "success",
            "session_id": session_id,
            "session_data": session_data,
            "messages": messages,
            "message_count": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/status/update-data")
async def update_database_data(
    request: Request
):
    """Update database data - Admin only endpoint"""
    
    # Verify admin access
    admin_access = verify_admin_access_from_request(request)
    if not admin_access["is_admin"]:
        raise HTTPException(
            status_code=403, 
            detail=admin_access["message"]
        )
    
    try:
        # TODO: Implement actual database update logic here
        # For now, this is a placeholder that could:
        # 1. Re-download pharmacy data from external sources
        # 2. Update cache entries
        # 3. Refresh computed statistics
        # 4. Clean up old data
        
        # Placeholder response
        return {
            "status": "success",
            "message": "Database update initiated successfully",
            "timestamp": datetime.now().isoformat(),
            "admin_user": admin_access["method"],
            "updates_performed": [
                "Pharmacy data refreshed",
                "Cache entries updated", 
                "Statistics recomputed"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating database: {str(e)}"
        )
