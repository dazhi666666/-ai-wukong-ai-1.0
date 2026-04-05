"""
缓存服务 - Redis + Memory 双层缓存
"""
import os
import json
import time
import hashlib
import logging
from typing import Any, Optional, Dict
from datetime import datetime
from functools import wraps
from app.services.logging_manager import get_logger

logger = get_logger("cache.service")

REDIS_AVAILABLE = False
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None


class CacheConfig:
    """缓存配置"""
    
    def __init__(self):
        self.redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        
        self.memory_cache_enabled = os.getenv("MEMORY_CACHE_ENABLED", "true").lower() == "true"
        self.memory_cache_max_size = int(os.getenv("MEMORY_CACHE_MAX_SIZE", "1000"))
        
        self.default_ttl = {
            "quotes": 60,
            "history": 1800,
            "financial": 86400,
            "news": 3600,
            "list": 86400,
        }
    
    def get_ttl(self, cache_type: str) -> int:
        return self.default_ttl.get(cache_type, 300)


_config = None


def get_cache_config() -> CacheConfig:
    global _config
    if _config is None:
        _config = CacheConfig()
    return _config


class MemoryCache:
    """内存缓存"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            entry = self.cache[key]
            if entry["expires_at"] > time.time():
                self.hits += 1
                return entry["value"]
            else:
                del self.cache[key]
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["created_at"])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate * 100, 2)
        }


class RedisCache:
    """Redis 缓存"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, password: str = "", db: int = 0):
        self.client = None
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self._connect()
    
    def _connect(self):
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available")
            return
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password if self.password else None,
                db=self.db,
                decode_responses=True
            )
            self.client.ping()
            logger.info(f"Redis connected: {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        if not self.client:
            return
        
        try:
            self.client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")
    
    def delete(self, key: str):
        if not self.client:
            return
        
        try:
            self.client.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")
    
    def clear(self):
        if not self.client:
            return
        
        try:
            self.client.flushdb()
        except Exception as e:
            logger.warning(f"Redis clear failed: {e}")
    
    def stats(self) -> Dict[str, Any]:
        if not self.client:
            return {"available": False}
        
        try:
            info = self.client.info("stats")
            return {
                "available": True,
                "keys": self.client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


class CacheService:
    """缓存服务 - 双层缓存"""
    
    def __init__(self):
        config = get_cache_config()
        
        self.redis_enabled = config.redis_enabled
        self.memory_cache_enabled = config.memory_cache_enabled
        
        self.memory_cache = MemoryCache(max_size=config.memory_cache_max_size) if self.memory_cache_enabled else None
        self.redis_cache = RedisCache(
            host=config.redis_host,
            port=config.redis_port,
            password=config.redis_password,
            db=config.redis_db
        ) if self.redis_enabled else None
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        key_parts = [prefix] + [str(arg) for arg in args]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        key_str = ":".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        if self.memory_cache:
            value = self.memory_cache.get(key)
            if value is not None:
                return value
        
        if self.redis_cache:
            value = self.redis_cache.get(key)
            if value is not None and self.memory_cache:
                self.memory_cache.set(key, value, 300)
            return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        if self.memory_cache:
            self.memory_cache.set(key, value, min(ttl, 300))
        
        if self.redis_cache:
            self.redis_cache.set(key, value, ttl)
    
    def delete(self, key: str):
        if self.memory_cache:
            self.memory_cache.delete(key)
        if self.redis_cache:
            self.redis_cache.delete(key)
    
    def clear(self):
        if self.memory_cache:
            self.memory_cache.clear()
        if self.redis_cache:
            self.redis_cache.clear()
    
    def clear_by_prefix(self, prefix: str):
        if self.memory_cache:
            keys_to_delete = [k for k in self.memory_cache.cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                self.memory_cache.delete(key)
        
        if self.redis_cache and self.redis_cache.client:
            try:
                pattern = f"*{prefix}*"
                for key in self.redis_cache.client.scan_iter(match=pattern):
                    self.redis_cache.delete(key)
            except Exception as e:
                logger.warning(f"Clear by prefix failed: {e}")
    
    def stats(self) -> Dict[str, Any]:
        return {
            "memory": self.memory_cache.stats() if self.memory_cache else {"enabled": False},
            "redis": self.redis_cache.stats() if self.redis_cache else {"enabled": False}
        }


_cache_service = None


def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(prefix: str, ttl: int = 300):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            key = cache._make_key(prefix, *args, **kwargs)
            
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator
