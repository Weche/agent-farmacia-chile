#!/usr/bin/env python3
"""
Cache Invalidation System
Monitors data changes and automatically invalidates stale cache entries
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import requests
import logging

from app.cache.redis_client import get_redis_client
from app.core.utils import get_env_value

logger = logging.getLogger(__name__)

class CacheInvalidationManager:
    """
    Manages automatic cache invalidation based on data freshness
    """
    
    def __init__(self):
        self.db_path = os.getenv('DATABASE_URL', 'pharmacy_finder.db')
        self.last_db_modified = None
        self.last_minsal_check = None
        self.check_interval = int(get_env_value("CACHE_HEALTH_CHECK_INTERVAL", "60"))
        self.auto_invalidate = get_env_value("AUTO_INVALIDATE_ON_DB_CHANGE", "true").lower() == "true"
        self.check_minsal_updates = get_env_value("CHECK_MINSAL_API_UPDATES", "true").lower() == "true"
        
    def get_db_modified_time(self) -> Optional[datetime]:
        """Get the last modification time of the database file"""
        try:
            if os.path.exists(self.db_path):
                timestamp = os.path.getmtime(self.db_path)
                return datetime.fromtimestamp(timestamp)
        except Exception as e:
            logger.error(f"❌ Error checking DB modification time: {e}")
        return None
    
    async def check_minsal_api_updates(self) -> Dict[str, Any]:
        """
        Check if MINSAL API has newer data than our cache
        """
        if not self.check_minsal_updates:
            return {"status": "disabled"}
        
        try:
            minsal_base = get_env_value("MINSAL_API_BASE", "https://midas.minsal.cl/farmacia_v2/WS")
            
            # Check both regular and turno endpoints
            endpoints = {
                "regular": f"{minsal_base}/getLocalesTurnos?dia=",
                "turno": f"{minsal_base}/getLocalesTurnos"
            }
            
            results = {}
            for endpoint_type, url in endpoints.items():
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            # Extract date from first record
                            first_record = data[0]
                            api_date = first_record.get('fecha_actualizacion', '')
                            results[endpoint_type] = {
                                "status": "ok",
                                "date": api_date,
                                "count": len(data)
                            }
                        else:
                            results[endpoint_type] = {"status": "no_data"}
                    else:
                        results[endpoint_type] = {"status": "error", "code": response.status_code}
                except Exception as e:
                    results[endpoint_type] = {"status": "error", "message": str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"❌ MINSAL API check error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def should_invalidate_cache(self) -> Dict[str, Any]:
        """
        Determine if cache should be invalidated based on various factors
        """
        invalidation_reasons = []
        
        # Check database modification
        current_db_modified = self.get_db_modified_time()
        if current_db_modified and current_db_modified != self.last_db_modified:
            invalidation_reasons.append({
                "reason": "database_modified",
                "details": f"DB modified at {current_db_modified}",
                "previous": self.last_db_modified
            })
            self.last_db_modified = current_db_modified
        
        # Check MINSAL API updates
        if self.check_minsal_updates:
            now = datetime.now()
            if not self.last_minsal_check or (now - self.last_minsal_check).seconds > 3600:  # Check every hour
                minsal_status = await self.check_minsal_api_updates()
                self.last_minsal_check = now
                
                if minsal_status.get("status") == "ok":
                    invalidation_reasons.append({
                        "reason": "minsal_api_check",
                        "details": "MINSAL API data available",
                        "minsal_data": minsal_status
                    })
        
        return {
            "should_invalidate": len(invalidation_reasons) > 0,
            "reasons": invalidation_reasons,
            "timestamp": datetime.now().isoformat()
        }
    
    async def perform_invalidation(self, reasons: list) -> Dict[str, Any]:
        """
        Execute cache invalidation based on provided reasons
        """
        redis_client = await get_redis_client()
        
        if not redis_client.redis_pool:
            return {"status": "redis_unavailable", "invalidated": 0}
        
        total_invalidated = 0
        
        # Invalidate based on reasons
        for reason in reasons:
            if reason["reason"] == "database_modified":
                # Invalidate all pharmacy data
                count = await redis_client.invalidate_all_pharmacy_data()
                total_invalidated += count
                logger.info(f"🔄 Invalidated {count} entries due to DB modification")
            
            elif reason["reason"] == "minsal_api_check":
                # Invalidate critical data (open-now, nearby)
                patterns = ["*api_open-now*", "*api_nearby*", "*api_stats*"]
                for pattern in patterns:
                    count = await redis_client.invalidate_pattern(pattern)
                    total_invalidated += count
                logger.info(f"🔄 Invalidated {total_invalidated} entries due to MINSAL API updates")
        
        return {
            "status": "completed",
            "invalidated": total_invalidated,
            "reasons": [r["reason"] for r in reasons],
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_invalidation_check(self) -> Dict[str, Any]:
        """
        Run a complete invalidation check cycle
        """
        try:
            # Check if invalidation is needed
            check_result = await self.should_invalidate_cache()
            
            if check_result["should_invalidate"] and self.auto_invalidate:
                # Perform invalidation
                invalidation_result = await self.perform_invalidation(check_result["reasons"])
                
                return {
                    "status": "invalidated",
                    "check_result": check_result,
                    "invalidation_result": invalidation_result
                }
            else:
                return {
                    "status": "no_invalidation_needed",
                    "check_result": check_result
                }
                
        except Exception as e:
            logger.error(f"❌ Invalidation check error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global invalidation manager
invalidation_manager = CacheInvalidationManager()

async def get_invalidation_manager() -> CacheInvalidationManager:
    """Get the global invalidation manager instance"""
    return invalidation_manager

async def manual_cache_invalidation() -> Dict[str, Any]:
    """
    Manually trigger cache invalidation (emergency function)
    """
    try:
        redis_client = await get_redis_client()  # This is async
        invalidated = redis_client.invalidate_all_pharmacy_data()  # This is sync
        
        return {
            "status": "manual_invalidation_completed", 
            "invalidated": invalidated,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Manual invalidation error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
