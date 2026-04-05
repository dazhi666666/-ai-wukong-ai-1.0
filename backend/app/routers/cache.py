"""
缓存管理 API 路由
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.logging_manager import get_logger

logger = get_logger("cache.router")

try:
    from app.services.cache.cache_service import get_cache_service, get_cache_config
    CACHE_AVAILABLE = True
except Exception as e:
    logger.error(f"Failed to import cache modules: {e}")
    CACHE_AVAILABLE = False
    get_cache_service = None
    get_cache_config = None

router = APIRouter(prefix="/api/cache", tags=["cache"])


class CacheClearRequest(BaseModel):
    prefix: str = None


@router.get("/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    service = get_cache_service()
    config = get_cache_config()
    
    return {
        "config": {
            "redis_enabled": config.redis_enabled,
            "memory_cache_enabled": config.memory_cache_enabled,
            "redis_host": config.redis_host,
            "redis_port": config.redis_port,
            "memory_cache_max_size": config.memory_cache_max_size,
            "default_ttl": config.default_ttl
        },
        "stats": service.stats()
    }


@router.post("/clear")
async def clear_cache(request: CacheClearRequest = None):
    """清除缓存"""
    service = get_cache_service()
    
    if request and request.prefix:
        service.clear_by_prefix(request.prefix)
        return {
            "message": f"Cache cleared for prefix: {request.prefix}",
            "prefix": request.prefix
        }
    
    service.clear()
    return {"message": "All cache cleared"}


@router.get("/config")
async def get_cache_config_info():
    """获取缓存配置"""
    config = get_cache_config()
    
    return {
        "redis_enabled": config.redis_enabled,
        "memory_cache_enabled": config.memory_cache_enabled,
        "redis_host": config.redis_host,
        "redis_port": config.redis_port,
        "memory_cache_max_size": config.memory_cache_max_size,
        "default_ttl": config.default_ttl
    }
