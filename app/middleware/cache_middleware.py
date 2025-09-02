#!/usr/bin/env python3
"""
Cache Middleware for FastAPI
Handles automatic caching and cache-aware responses
"""

import json
import time
from datetime import datetime
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

from app.cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)

class CacheMiddleware:
    """
    FastAPI middleware for intelligent caching with freshness guarantees
    """
    
    def __init__(self, app):
        self.app = app
        
        # Endpoints that should be cached
        self.cacheable_endpoints = {
            "/api/search",
            "/api/open-now", 
            "/api/nearby",
            "/api/stats",
            "/api/communes"
        }
        
        # Endpoints that should bypass cache (always fresh)
        self.bypass_cache_endpoints = {
            "/health",
            "/docs",
            "/openapi.json"
        }
    
    async def __call__(self, request: Request, call_next: Callable):
        """
        Process request with intelligent caching
        """
        start_time = time.time()
        
        # Check if this endpoint should be cached
        path = request.url.path
        should_cache = any(endpoint in path for endpoint in self.cacheable_endpoints)
        should_bypass = any(endpoint in path for endpoint in self.bypass_cache_endpoints)
        
        if not should_cache or should_bypass:
            # Pass through without caching
            response = await call_next(request)
            return response
        
        # Try to get cached response
        redis_client = await get_redis_client()
        cache_key = self._generate_cache_key(request)
        cached_result = None
        
        if redis_client.redis_pool:
            cached_result = await redis_client.get_cached_data(cache_key)
        
        if cached_result and not cached_result.get('is_stale', False):
            # Return cached response with cache headers
            response_data = cached_result['data']
            
            # Add cache metadata to response
            if isinstance(response_data, dict):
                response_data['_cache_info'] = {
                    'cached': True,
                    'cached_at': cached_result['cached_at'].isoformat(),
                    'age_seconds': cached_result['age_seconds']
                }
            
            response = JSONResponse(
                content=response_data,
                headers={
                    "X-Cache": "HIT",
                    "X-Cache-Age": str(int(cached_result['age_seconds'])),
                    "X-Cache-TTL": str(redis_client.get_ttl_for_endpoint(path))
                }
            )
            
            logger.info(f"✅ Cache HIT for {path} (age: {cached_result['age_seconds']:.1f}s)")
            return response
        
        # Cache miss - get fresh data
        response = await call_next(request)
        
        # Cache the response if it's successful
        if response.status_code == 200 and redis_client.redis_pool:
            try:
                # Extract response data
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                response_data = json.loads(response_body.decode())
                
                # Add freshness metadata
                if isinstance(response_data, dict):
                    response_data['_cache_info'] = {
                        'cached': False,
                        'generated_at': datetime.now().isoformat(),
                        'fresh': True
                    }
                
                # Cache the response
                ttl = redis_client.get_ttl_for_endpoint(path)
                await redis_client.set_cached_data(cache_key, response_data, ttl)
                
                # Create new response with updated data
                response = JSONResponse(
                    content=response_data,
                    headers={
                        "X-Cache": "MISS",
                        "X-Cache-TTL": str(ttl),
                        "X-Response-Time": f"{(time.time() - start_time) * 1000:.1f}ms"
                    }
                )
                
                logger.info(f"✅ Cache MISS for {path} - cached with TTL {ttl}s")
                
            except Exception as e:
                logger.error(f"❌ Caching error for {path}: {e}")
                # Return original response if caching fails
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate cache key from request path and parameters
        """
        # Import here to avoid circular imports
        from app.cache.redis_client import RedisClient
        
        redis_client = RedisClient()
        
        # Extract query parameters
        params = dict(request.query_params)
        
        # Generate key using redis client method
        return redis_client.generate_cache_key(request.url.path, params)

async def cache_warmup():
    """
    Warm up cache with frequently accessed data
    """
    redis_client = await get_redis_client()
    
    if not redis_client.redis_pool:
        logger.warning("⚠️  Cache warmup skipped - Redis unavailable")
        return
    
    logger.info("🔥 Starting cache warmup...")
    
    try:
        # Import here to avoid circular imports
        from app.database import PharmacyDatabase
        
        db = PharmacyDatabase()
        
        # Warm up commune list (static data)
        communes = db.get_all_communes()
        redis_client.set_cached_data(
            "api_communes",
            communes,
            redis_client.ttl_medium
        )
        
        # Warm up stats (changes frequently but commonly requested)
        stats = db.get_pharmacy_count()
        redis_client.set_cached_data(
            "api_stats",
            stats,
            redis_client.ttl_high
        )
        
        # Warm up popular communes (Santiago, Las Condes, Providencia)
        popular_communes = ["SANTIAGO", "LAS CONDES", "PROVIDENCIA", "MAIPU", "VIÑA DEL MAR"]
        
        for comuna in popular_communes:
            try:
                pharmacies = db.find_by_comuna(comuna)
                cache_key = redis_client.generate_cache_key("/api/search", {"comuna": comuna})
                redis_client.set_cached_data(
                    cache_key,
                    pharmacies,
                    redis_client.ttl_high
                )
            except Exception as e:
                logger.error(f"❌ Warmup error for {comuna}: {e}")
        
        logger.info(f"🔥 Cache warmup completed - {len(popular_communes)} communes preloaded")
        
    except Exception as e:
        logger.error(f"❌ Cache warmup failed: {e}")

async def cache_health_check() -> Dict[str, Any]:
    """
    Check cache system health and performance
    """
    redis_client = await get_redis_client()
    
    health_info = {
        "timestamp": datetime.now().isoformat(),
        "redis_available": bool(redis_client.redis_pool),
        "cache_stats": redis_client.get_cache_stats()
    }
    
    if redis_client.redis_pool:
        try:
            # Test cache operations
            test_key = "health_check_test"
            test_data = {"test": True, "timestamp": datetime.now().isoformat()}
            
            # Test write
            write_success = redis_client.set_cached_data(test_key, test_data, 60)
            
            # Test read
            read_result = redis_client.get_cached_data(test_key)
            read_success = read_result is not None
            
            # Clean up
            if redis_client.redis_pool:
                redis_client.redis_pool.delete(test_key)
            
            health_info.update({
                "write_test": write_success,
                "read_test": read_success,
                "operations_healthy": write_success and read_success
            })
            
        except Exception as e:
            health_info.update({
                "operations_healthy": False,
                "error": str(e)
            })
    
    return health_info
