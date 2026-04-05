"""
YFinance 数据提供者 - 美股/港股
"""
import os
import asyncio
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date
import logging

from .base import BaseStockProvider
from app.services.logging_manager import get_logger

logger = get_logger("stock_data.yfinance")

YFINANCE_AVAILABLE = False
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None


class YFinanceProvider(BaseStockProvider):
    """YFinance 股票数据提供者"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("YFinance")
        self.config = config or {}
    
    async def connect(self) -> bool:
        """连接到 YFinance"""
        if not YFINANCE_AVAILABLE:
            self.logger.error("YFinance library not installed")
            return False
        
        try:
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            if info:
                self.connected = True
                self.logger.info("YFinance connected successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"YFinance connection failed: {e}")
            return False
    
    def is_available(self) -> bool:
        return YFINANCE_AVAILABLE and self.connected
    
    async def get_stock_basic(self, symbol: str = None) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """获取股票基础信息"""
        if not self.is_available():
            return None
        
        try:
            if not symbol:
                return []
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            return {
                "symbol": symbol,
                "name": info.get("shortName", ""),
                "industry": info.get("industry", ""),
                "sector": info.get("sector", ""),
                "market_cap": info.get("marketCap"),
                "data_source": "yfinance"
            }
            
        except Exception as e:
            self.logger.error(f"Get stock basic failed: {e}")
            return None
    
    async def get_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情"""
        if not self.is_available():
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            return self.standardize_quotes({
                "symbol": symbol,
                "name": info.get("shortName", ""),
                "close": info.get("currentPrice"),
                "open": info.get("open"),
                "high": info.get("dayHigh"),
                "low": info.get("dayLow"),
                "pre_close": info.get("previousClose"),
                "volume": info.get("volume"),
                "market_cap": info.get("marketCap"),
                "trade_date": datetime.now().strftime('%Y-%m-%d')
            })
            
        except Exception as e:
            self.logger.error(f"Get quotes failed: {e}")
            return None
    
    async def get_historical(
        self,
        symbol: str,
        start_date: Union[str, date],
        end_date: Union[str, date] = None,
        period: str = "daily"
    ) -> Optional[Any]:
        """获取历史数据"""
        if not self.is_available():
            return None
        
        try:
            start_str = self._format_date(start_date)
            end_str = self._format_date(end_date) if end_date else datetime.now().strftime('%Y-%m-%d')
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_str, end=end_str, interval=period)
            
            if df is not None and not df.empty:
                self.logger.info(f"Got {len(df)} historical records for {symbol}")
                return df
            
            return None
            
        except Exception as e:
            self.logger.error(f"Get historical failed: {e}")
            return None
    
    async def get_stock_list(self, market: str = None) -> Optional[List[Dict[str, Any]]]:
        """获取股票列表 - YFinance 不支持获取全量列表"""
        return []
    
    async def get_news(self, symbol: str = None, hours_back: int = 24, max_news: int = 10) -> Optional[List[Dict[str, Any]]]:
        """获取股票新闻"""
        if not self.is_available() or not symbol:
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return []
            
            news_list = []
            for item in news[:max_news]:
                news_list.append({
                    "title": item.get("title", ""),
                    "content": item.get("summary", ""),
                    "source": item.get("source", "Yahoo Finance"),
                    "publish_time": item.get("providerPublishTime", ""),
                    "url": item.get("link", ""),
                    "data_source": "yfinance"
                })
            
            return news_list
            
        except Exception as e:
            self.logger.error(f"Get news failed: {e}")
            return None
