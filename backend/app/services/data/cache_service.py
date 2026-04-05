"""
数据缓存服务
支持 SQLite 和 Redis 双缓存
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from functools import wraps

from app.database.session import SessionLocal
from app.models.data_cache import DataCache
from app.services.logging_manager import get_logger

logger = get_logger("data.cache_service")

# 缓存时间配置（很长）
CACHE_TTL = {
    "quote": 15 * 60,        # 实时行情 15分钟
    "daily": 7 * 24 * 60 * 60,   # 日线数据 7天
    "indicator": 7 * 24 * 60 * 60,  # 财务指标 7天
    "moneyflow": 7 * 24 * 60 * 60,  # 资金流向 7天
    "margin": 7 * 24 * 60 * 60,    # 融资融券 7天
    "leaderboard": 7 * 24 * 60 * 60,  # 龙虎榜 7天
}

# Redis 客户端
_redis_client = None
_redis_available = None


def get_redis_client():
    """获取 Redis 客户端"""
    global _redis_client, _redis_available
    
    if _redis_available is False:
        return None
    
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=1
            )
            _redis_client.ping()
            _redis_available = True
            logger.info("✅ Redis 缓存已启用")
        except Exception as e:
            _redis_available = False
            _redis_client = None
            logger.info(f"ℹ️ Redis 不可用，使用 SQLite 缓存: {e}")
    
    return _redis_client


def generate_cache_key(data_type: str, stock_code: str = "", **kwargs) -> str:
    """生成缓存键"""
    if stock_code:
        return f"{data_type}:{stock_code}"
    return f"{data_type}:default"


def get_cache_ttl(data_type: str) -> int:
    """获取缓存有效期（秒）"""
    return CACHE_TTL.get(data_type, 3600)


class CacheService:
    """缓存服务类"""
    
    def __init__(self):
        self.use_redis = get_redis_client() is not None
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存数据或 None
        """
        # 优先从 Redis 获取
        if self.use_redis and _redis_client:
            try:
                data = _redis_client.get(cache_key)
                if data:
                    # 更新命中计数
                    self._update_hit_count_sqlite(cache_key, increment=True)
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis 获取缓存失败: {e}")
        
        # 回退到 SQLite
        return self._get_from_sqlite(cache_key)
    
    def set(self, cache_key: str, data: Dict[str, Any], data_type: str = "default") -> bool:
        """
        设置缓存
        
        Args:
            cache_key: 缓存键
            data: 缓存数据
            data_type: 数据类型
            
        Returns:
            是否成功
        """
        ttl = get_cache_ttl(data_type)
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # 优先存入 Redis
        if self.use_redis and _redis_client:
            try:
                _redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(data, ensure_ascii=False, default=str)
                )
                logger.debug(f"✅ Redis 缓存已设置: {cache_key}")
            except Exception as e:
                logger.warning(f"Redis 设置缓存失败: {e}")
        
        # 同时存入 SQLite 作为备份
        return self._save_to_sqlite(cache_key, data, data_type, expires_at)
    
    def delete(self, cache_key: str) -> bool:
        """
        删除缓存
        
        Args:
            cache_key: 缓存键
            
        Returns:
            是否成功
        """
        # 删除 Redis
        if self.use_redis and _redis_client:
            try:
                _redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Redis 删除缓存失败: {e}")
        
        # 删除 SQLite
        return self._delete_from_sqlite(cache_key)
    
    def clear_all(self) -> bool:
        """清空所有缓存"""
        if self.use_redis and _redis_client:
            try:
                _redis_client.flushdb()
                logger.info("✅ Redis 缓存已清空")
            except Exception as e:
                logger.warning(f"Redis 清空缓存失败: {e}")
        
        # 清空 SQLite
        return self._clear_sqlite()
    
    def get_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        status = {
            "backend": "redis" if self.use_redis else "sqlite",
            "redis_available": self.use_redis,
            "cache_ttl": CACHE_TTL
        }
        
        # SQLite 统计
        try:
            db = SessionLocal()
            total = db.query(DataCache).count()
            expired = db.query(DataCache).filter(
                DataCache.expires_at < datetime.now()
            ).count()
            status["sqlite"] = {
                "total": total,
                "expired": expired,
                "valid": total - expired
            }
            db.close()
        except Exception as e:
            logger.warning(f"获取 SQLite 缓存状态失败: {e}")
        
        return status
    
    # SQLite 方法
    def _get_from_sqlite(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从 SQLite 获取缓存"""
        try:
            db = SessionLocal()
            cache = db.query(DataCache).filter(
                DataCache.cache_key == cache_key,
                DataCache.expires_at > datetime.now()
            ).first()
            
            if cache:
                # 更新命中计数
                if cache.hit_count is not None:
                    cache.hit_count += 1
                    db.commit()
                
                db.close()
                return cache.data
            
            db.close()
        except Exception as e:
            logger.warning(f"SQLite 获取缓存失败: {e}")
        
        return None
    
    def _save_to_sqlite(self, cache_key: str, data: Dict[str, Any], data_type: str, expires_at: datetime) -> bool:
        """保存到 SQLite"""
        try:
            db = SessionLocal()
            
            # 检查是否已存在
            existing = db.query(DataCache).filter(
                DataCache.cache_key == cache_key
            ).first()
            
            if existing:
                existing.data = data
                existing.expires_at = expires_at
                existing.updated_at = datetime.now()
            else:
                # 提取 stock_code
                stock_code = ""
                if ":" in cache_key:
                    parts = cache_key.split(":")
                    if len(parts) >= 2:
                        stock_code = parts[1]
                
                new_cache = DataCache(
                    cache_key=cache_key,
                    data_type=data_type,
                    stock_code=stock_code,
                    data=data,
                    expires_at=expires_at,
                    hit_count=0
                )
                db.add(new_cache)
            
            db.commit()
            db.close()
            logger.debug(f"✅ SQLite 缓存已保存: {cache_key}")
            return True
        except Exception as e:
            logger.warning(f"SQLite 保存缓存失败: {e}")
        
        return False
    
    def _delete_from_sqlite(self, cache_key: str) -> bool:
        """从 SQLite 删除"""
        try:
            db = SessionLocal()
            db.query(DataCache).filter(
                DataCache.cache_key == cache_key
            ).delete()
            db.commit()
            db.close()
            return True
        except Exception as e:
            logger.warning(f"SQLite 删除缓存失败: {e}")
        
        return False
    
    def _clear_sqlite(self) -> bool:
        """清空 SQLite"""
        try:
            db = SessionLocal()
            db.query(DataCache).delete()
            db.commit()
            db.close()
            logger.info("✅ SQLite 缓存已清空")
            return True
        except Exception as e:
            logger.warning(f"SQLite 清空缓存失败: {e}")
        
        return False
    
    def _update_hit_count_sqlite(self, cache_key: str, increment: bool = False):
        """更新 SQLite 命中计数"""
        try:
            db = SessionLocal()
            cache = db.query(DataCache).filter(
                DataCache.cache_key == cache_key
            ).first()
            
            if cache:
                if increment:
                    cache.hit_count = (cache.hit_count or 0) + 1
                db.commit()
            
            db.close()
        except Exception:
            pass


# 全局缓存服务实例
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """获取缓存服务单例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# 缓存装饰器
def cached(data_type: str, key_param: str = "stock_code"):
    """
    缓存装饰器
    
    Usage:
        @cached("quote", key_param="stock_code")
        def get_quote(stock_code: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # 获取股票代码作为缓存键
            if key_param in kwargs:
                stock_code = kwargs[key_param]
            elif len(args) > 0:
                stock_code = args[0]
            else:
                stock_code = ""
            
            cache_key = generate_cache_key(data_type, stock_code)
            
            # 尝试获取缓存
            force_refresh = kwargs.get('force_refresh', False)
            if not force_refresh:
                cached_data = cache.get(cache_key)
                if cached_data:
                    logger.info(f"📦 使用缓存: {cache_key}")
                    return cached_data
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 保存缓存
            if result is not None:
                cache.set(cache_key, result, data_type)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # 获取股票代码作为缓存键
            if key_param in kwargs:
                stock_code = kwargs[key_param]
            elif len(args) > 0:
                stock_code = args[0]
            else:
                stock_code = ""
            
            cache_key = generate_cache_key(data_type, stock_code)
            
            # 尝试获取缓存
            force_refresh = kwargs.get('force_refresh', False)
            if not force_refresh:
                cached_data = cache.get(cache_key)
                if cached_data:
                    logger.info(f"📦 使用缓存: {cache_key}")
                    return cached_data
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 保存缓存
            if result is not None:
                cache.set(cache_key, result, data_type)
            
            return result
        
        # 判断是异步还是同步函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
