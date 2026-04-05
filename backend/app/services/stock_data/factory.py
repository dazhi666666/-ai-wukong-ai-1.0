"""
股票数据提供者工厂
"""
import os
import json
import logging
from typing import Dict, Optional, Any

from .providers.base import BaseStockProvider
from .providers.tushare import TushareProvider
from .providers.akshare import AKShareProvider
from .providers.baostock import BaoStockProvider
from .providers.yfinance import YFinanceProvider
from .providers.juhe import JuheProvider
from app.services.logging_manager import get_logger

logger = get_logger("stock_data.factory")

PROVIDER_CLASSES: Dict[str, type] = {}

def _load_providers():
    """Lazy load providers to avoid import errors"""
    global PROVIDER_CLASSES
    if PROVIDER_CLASSES:
        return
    
    try:
        from .providers.tushare import TushareProvider
        PROVIDER_CLASSES["tushare"] = TushareProvider
    except ImportError as e:
        logger.warning(f"Tushare provider not available: {e}")
    
    try:
        from .providers.akshare import AKShareProvider
        PROVIDER_CLASSES["akshare"] = AKShareProvider
    except ImportError as e:
        logger.warning(f"AKShare provider not available: {e}")
    
    try:
        from .providers.baostock import BaoStockProvider
        PROVIDER_CLASSES["baostock"] = BaoStockProvider
    except ImportError as e:
        logger.warning(f"BaoStock provider not available: {e}")
    
    try:
        from .providers.yfinance import YFinanceProvider
        PROVIDER_CLASSES["yfinance"] = YFinanceProvider
    except ImportError as e:
        logger.warning(f"YFinance provider not available: {e}")

    try:
        from .providers.juhe import JuheProvider
        PROVIDER_CLASSES["juhe"] = JuheProvider
    except ImportError as e:
        logger.warning(f"Juhe provider not available: {e}")

_load_providers()

PROVIDER_DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {
    "tushare": {
        "timeout": 30,
        "max_retries": 3,
    },
    "akshare": {
        "timeout": 30,
    },
    "baostock": {
        "timeout": 30,
    },
    "yfinance": {
        "timeout": 30,
    },
    "juhe": {
        "timeout": 30,
    },
}

_provider_instances: Dict[str, BaseStockProvider] = {}


def get_provider_config_from_file(provider_name: str) -> Optional[Dict[str, Any]]:
    """从配置文件获取 Provider 配置"""
    try:
        import os
        from pathlib import Path
        
        config_file = Path(__file__).parent.parent.parent / 'stock_config.json'
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
                return configs.get(provider_name)
    except Exception as e:
        logger.debug(f"Could not get provider config from file: {e}")
    
    return None


def get_provider_config_from_db(provider_name: str) -> Optional[Dict[str, Any]]:
    """从数据库获取 Provider 配置"""
    try:
        from app.database.session import SessionLocal
        from app.models.config import LLMProvider
        
        db = SessionLocal()
        try:
            provider_obj = db.query(LLMProvider).filter(
                LLMProvider.name == provider_name
            ).first()
            
            if provider_obj:
                return {
                    "api_key": provider_obj.api_key,
                    "api_secret": provider_obj.api_secret,
                    "is_active": provider_obj.is_active,
                }
        finally:
            db.close()
    except Exception as e:
        logger.debug(f"Could not get provider config from DB: {e}")
    
    return None


class StockDataFactory:
    """股票数据提供者工厂"""
    
    @classmethod
    def create(
        cls,
        provider_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseStockProvider]:
        """创建数据提供者实例"""
        provider_class = PROVIDER_CLASSES.get(provider_name.lower())
        
        if not provider_class:
            logger.warning(f"Unknown provider: {provider_name}")
            return None
        
        provider_config = PROVIDER_DEFAULT_CONFIG.get(provider_name.lower(), {})
        if config:
            provider_config.update(config)
        
        file_config = get_provider_config_from_file(provider_name.lower())
        if file_config and file_config.get("api_key"):
            if not config:
                config = {}
            config["api_key"] = file_config["api_key"]
        
        try:
            if provider_name.lower() == "tushare":
                token = os.getenv("TUSHARE_TOKEN", "")
                if config and config.get("api_key"):
                    token = config["api_key"]
                instance = provider_class(token=token, config=provider_config)
            elif provider_name.lower() == "juhe":
                api_key = os.getenv("JUHE_API_KEY", "")
                if file_config and file_config.get("api_key"):
                    api_key = file_config["api_key"]
                instance = provider_class(api_key=api_key, config=provider_config)
            else:
                instance = provider_class(config=provider_config)
            
            return instance
        except Exception as e:
            logger.error(f"Failed to create provider {provider_name}: {e}")
            return None
    
    @classmethod
    def get_provider(
        cls,
        provider_name: str,
        config: Optional[Dict[str, Any]] = None,
        force_new: bool = False
    ) -> Optional[BaseStockProvider]:
        """获取数据提供者实例（带缓存）"""
        key = provider_name.lower()
        
        if force_new or key not in _provider_instances:
            _provider_instances[key] = cls.create(provider_name, config)
        
        return _provider_instances.get(key)
    
    @classmethod
    def get_all_providers(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有可用提供者信息"""
        return {
            name: {
                "name": name,
                "class": cls.__name__,
                "available": name in PROVIDER_CLASSES
            }
            for name in PROVIDER_CLASSES.keys()
        }
    
    @classmethod
    def clear_cache(cls):
        """清除缓存的提供者实例"""
        global _provider_instances
        _provider_instances = {}


def get_stock_provider(
    provider_name: str = "tushare",
    config: Optional[Dict[str, Any]] = None,
    force_new: bool = False
) -> Optional[BaseStockProvider]:
    """便捷函数：获取股票数据提供者"""
    return StockDataFactory.get_provider(provider_name, config, force_new)
