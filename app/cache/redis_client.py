#!/usr/bin/env python3
"""
Redis Cache Client with Smart Invalidation
Handles connection, caching, and automatic invalidation for pharmacy data
"""

import redis
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from app.core.utils import get_env_value
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisClient:
    """
    Smart Redis cache client with automatic invalidation and fallback support
    """
    
    def __init__(self):
        self.redis_pool = None
        self.redis_url = get_env_value("REDIS_URL")
        self.fallback_enabled = get_env_value("FALLBACK_TO_SQLITE", "true").lower() == "true"
        self.max_stale_age = int(get_env_value("MAX_STALE_AGE_SECONDS", "3600"))
        
        # TTL settings from environment
        self.ttl_critical = int(get_env_value("CACHE_TTL_CRITICAL", "300"))
        self.ttl_high = int(get_env_value("CACHE_TTL_HIGH", "1800"))
        self.ttl_medium = int(get_env_value("CACHE_TTL_MEDIUM", "21600"))
        self.ttl_low = int(get_env_value("CACHE_TTL_LOW", "86400"))
        
    async def connect(self):
        """Initialize Redis connection pool"""
        try:
            self.redis_pool = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_pool.ping()
            logger.info("✅ Redis connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            if self.fallback_enabled:
                logger.info("🔄 Continuing with SQLite fallback")
            return False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_pool:
            self.redis_pool.close()
            logger.info("🔌 Redis connection closed")
    
    def get_ttl_for_endpoint(self, endpoint: str) -> int:
        """
        Get appropriate TTL based on endpoint criticality
        """
        critical_endpoints = ["/api/open-now", "/api/nearby"]
        high_endpoints = ["/api/search", "/api/stats"]
        medium_endpoints = ["/api/communes"]
        
        if any(ep in endpoint for ep in critical_endpoints):
            return self.ttl_critical
        elif any(ep in endpoint for ep in high_endpoints):
            return self.ttl_high
        elif any(ep in endpoint for ep in medium_endpoints):
            return self.ttl_medium
        else:
            return self.ttl_low
    
    def generate_cache_key(self, endpoint: str, params: Dict[str, Any] = None) -> str:
        """
        Generate consistent cache key from endpoint and parameters
        """
        key_parts = [endpoint.replace("/", "_")]
        
        if params:
            # Sort parameters for consistent key generation
            sorted_params = sorted(params.items())
            param_str = "_".join([f"{k}:{v}" for k, v in sorted_params if v is not None])
            if param_str:
                key_parts.append(param_str)
        
        # Add current hour for time-sensitive data (open/closed status)
        if "open-now" in endpoint or "nearby" in endpoint:
            current_hour = datetime.now().strftime("%Y%m%d_%H")
            key_parts.append(f"hour:{current_hour}")
        
        return ":".join(key_parts)
    
    def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from cache with freshness validation
        """
        if not self.redis_pool:
            return None
        
        try:
            # Get cached data and metadata
            cached_data = self.redis_pool.hgetall(cache_key)
            
            if not cached_data or 'data' not in cached_data:
                return None
            
            # Check data freshness
            cache_timestamp = datetime.fromisoformat(cached_data.get('timestamp', ''))
            age_seconds = (datetime.now() - cache_timestamp).total_seconds()
            
            # Return data with metadata
            return {
                'data': json.loads(cached_data['data']),
                'cached_at': cache_timestamp,
                'age_seconds': age_seconds,
                'is_stale': age_seconds > self.max_stale_age
            }
            
        except Exception as e:
            logger.error(f"❌ Cache retrieval error for {cache_key}: {e}")
            return None
    
    def set_cached_data(self, cache_key: str, data: Any, ttl_seconds: int = None) -> bool:
        """
        Store data in cache with metadata
        """
        if not self.redis_pool:
            return False
        
        try:
            # Prepare cache entry with metadata
            cache_entry = {
                'data': json.dumps(data, default=str),
                'timestamp': datetime.now().isoformat(),
                'ttl': ttl_seconds or self.ttl_high
            }
            
            # Store in Redis with expiration
            self.redis_pool.hset(cache_key, mapping=cache_entry)
            if ttl_seconds:
                self.redis_pool.expire(cache_key, ttl_seconds)
            
            logger.info(f"✅ Cached data for {cache_key} (TTL: {ttl_seconds}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache storage error for {cache_key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching a pattern
        """
        if not self.redis_pool:
            return 0
        
        try:
            keys = self.redis_pool.keys(pattern)
            if keys:
                deleted = self.redis_pool.delete(*keys)
                logger.info(f"🗑️  Invalidated {deleted} cache entries matching '{pattern}'")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"❌ Cache invalidation error for pattern '{pattern}': {e}")
            return 0
    
    def invalidate_all_pharmacy_data(self) -> int:
        """
        Invalidate all pharmacy-related cache entries
        """
        patterns = [
            "*api_search*",
            "*api_open-now*", 
            "*api_nearby*",
            "*api_stats*"
        ]
        
        total_invalidated = 0
        for pattern in patterns:
            total_invalidated += self.invalidate_pattern(pattern)
        
        logger.info(f"🔄 Total invalidated: {total_invalidated} pharmacy cache entries")
        return total_invalidated
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get Redis cache statistics
        """
        if not self.redis_pool:
            return {"status": "disconnected"}
        
        try:
            info = self.redis_pool.info()
            
            return {
                "status": "connected",
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Cache stats error: {e}")
            return {"status": "error", "message": str(e)}

# Global Redis client instance
redis_client = RedisClient()

async def get_redis_client() -> RedisClient:
    """Get the global Redis client instance"""
    return redis_client
