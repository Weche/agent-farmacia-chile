"""
System Status and Health Dashboard API
Provides comprehensive system health information
"""
from fastapi import APIRouter, Depends
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
        redis_client.ping()
        
        # Get Redis info
        info = redis_client.info()
        
        # Get cache statistics
        cache_keys = redis_client.keys("*")
        
        # Group keys by type
        key_types = {}
        for key in cache_keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
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
        
        # Environment variables (safe ones)
        env_vars = {
            "OPENAI_API_KEY": "Set" if os.getenv("OPENAI_API_KEY") else "Not Set",
            "GOOGLE_MAPS_API_KEY": "Set" if os.getenv("GOOGLE_MAPS_API_KEY") else "Not Set",
            "REDIS_URL": os.getenv("REDIS_URL", "default"),
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
