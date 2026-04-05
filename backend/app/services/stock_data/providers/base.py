"""
股票数据提供者基类
定义所有数据源提供者的统一接口
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date
import logging

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

from app.services.logging_manager import get_logger


class BaseStockProvider(ABC):
    """股票数据提供者基类"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.connected = False
        self.logger = get_logger(f"stock_data.{provider_name}")
        self.config: Dict[str, Any] = {}
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接到数据源"""
        pass
    
    async def disconnect(self):
        """断开连接"""
        self.connected = False
        self.logger.info(f"{self.provider_name} disconnected")
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return self.connected
    
    @abstractmethod
    async def get_stock_basic(self, symbol: str = None) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """获取股票基础信息"""
        pass
    
    @abstractmethod
    async def get_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情"""
        pass
    
    @abstractmethod
    async def get_historical(
        self, 
        symbol: str, 
        start_date: Union[str, date], 
        end_date: Union[str, date] = None,
        period: str = "daily"
    ) -> Optional[pd.DataFrame]:
        """获取历史数据"""
        pass
    
    async def get_stock_list(self, market: str = None) -> Optional[List[Dict[str, Any]]]:
        """获取股票列表"""
        return await self.get_stock_basic()
    
    async def get_financial(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取财务数据（可选实现）"""
        return None
    
    async def get_news(self, symbol: str = None, hours_back: int = 24, max_news: int = 10) -> Optional[List[Dict[str, Any]]]:
        """获取股票新闻（可选实现）"""
        return None
    
    def standardize_basic_info(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化股票基础信息"""
        return {
            "code": raw_data.get("code", raw_data.get("symbol", "")),
            "name": raw_data.get("name", ""),
            "symbol": raw_data.get("symbol", raw_data.get("code", "")),
            "full_symbol": raw_data.get("full_symbol", ""),
            "industry": raw_data.get("industry"),
            "area": raw_data.get("area"),
            "market": raw_data.get("market"),
            "list_date": raw_data.get("list_date"),
            "data_source": self.provider_name.lower(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    def standardize_quotes(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化行情数据"""
        symbol = raw_data.get("symbol", raw_data.get("code", ""))
        return {
            "symbol": symbol,
            "full_symbol": raw_data.get("full_symbol", symbol),
            "close": self._convert_to_float(raw_data.get("close")),
            "open": self._convert_to_float(raw_data.get("open")),
            "high": self._convert_to_float(raw_data.get("high")),
            "low": self._convert_to_float(raw_data.get("low")),
            "pre_close": self._convert_to_float(raw_data.get("pre_close")),
            "change": self._convert_to_float(raw_data.get("change")),
            "pct_chg": self._convert_to_float(raw_data.get("pct_chg")),
            "volume": self._convert_to_float(raw_data.get("volume")),
            "amount": self._convert_to_float(raw_data.get("amount")),
            "trade_date": raw_data.get("trade_date"),
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": self.provider_name.lower()
        }
    
    def _convert_to_float(self, value: Any) -> Optional[float]:
        """转换为浮点数"""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _format_date(self, date_value: Union[str, date, None]) -> Optional[str]:
        """格式化日期"""
        if not date_value:
            return None
        if isinstance(date_value, date):
            return date_value.strftime('%Y-%m-%d')
        return str(date_value)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.provider_name}', connected={self.connected})>"
