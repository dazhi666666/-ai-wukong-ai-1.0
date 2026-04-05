"""
AKShare 数据提供者 - A股/港股/期货等
"""
import os
import asyncio
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date, timedelta
import pandas as pd
import logging
import time
from functools import lru_cache

from .base import BaseStockProvider
from app.services.logging_manager import get_logger

logger = get_logger("stock_data.akshare")

AKSHARE_AVAILABLE = False
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    ak = None


def _akshare_call(func, retries=3, delay=2, timeout=15, **kwargs):
    """调用 AkShare 函数，带重试机制和超时"""
    last_error = None
    for attempt in range(retries):
        try:
            return func(**kwargs)
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            # 网络错误才重试
            if any(x in err_str for x in ['connection', 'timeout', 'remote', 'network']):
                if attempt < retries - 1:
                    logger.warning(f"AkShare 网络错误，{delay}秒后重试 ({attempt+1}/{retries}): {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"AkShare 网络错误重试失败 ({retries}次): {e}")
            else:
                # 非网络错误直接抛出
                logger.error(f"AkShare 调用错误 (不重试): {e}")
                break
    raise last_error if last_error else Exception("Unknown error")


class AKShareProvider(BaseStockProvider):
    """AKShare 股票数据提供者"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("AKShare")
        self.config = config or {}
        self._connection_tested = False
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._cache_ttl = 60  # 缓存60秒
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """设置缓存"""
        self._cache[key] = (data, time.time())
    
    async def connect(self) -> bool:
        """连接到 AKShare - 使用更轻量的方式验证"""
        if not AKSHARE_AVAILABLE:
            self.logger.error("AKShare library not installed")
            return False
        
        # 尝试获取一只股票的数据来验证连接
        test_symbols = ["000001", "600519"]
        for symbol in test_symbols:
            try:
                df = await asyncio.to_thread(
                    _akshare_call, 
                    ak.stock_zh_a_hist,
                    retries=2,
                    delay=1,
                    symbol=symbol,
                    start_date=(datetime.now() - timedelta(days=5)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d'),
                    adjust=""
                )
                if df is not None and not df.empty:
                    self.connected = True
                    self._connection_tested = True
                    self.logger.info(f"AKShare connected successfully (tested with {symbol})")
                    return True
            except Exception as e:
                self.logger.warning(f"AKShare connection test failed for {symbol}: {e}")
                continue
        
        self.logger.error(f"AKShare connection failed: all test symbols failed")
        self.connected = False
        return False
    
    def is_available(self) -> bool:
        return AKSHARE_AVAILABLE and self.connected
    
    async def get_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情 - 带缓存和重试"""
        if not self.is_available():
            return None
        
        # 尝试从缓存获取
        cache_key = f"quote_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # 尝试获取实时行情，带重试
            df = await asyncio.to_thread(
                _akshare_call,
                ak.stock_zh_a_spot_em,
                retries=3,
                delay=2
            )
            if df is None or df.empty:
                return None
            
            stock_row = df[df["代码"] == symbol]
            if stock_row.empty:
                return None
            
            row = stock_row.iloc[0]
            result = self.standardize_quotes({
                "symbol": symbol,
                "name": row.get("名称", ""),
                "close": row.get("最新价"),
                "open": row.get("今开"),
                "high": row.get("最高"),
                "low": row.get("最低"),
                "pre_close": row.get("昨收"),
                "volume": row.get("成交量"),
                "amount": row.get("成交额"),
                "change": row.get("涨跌额"),
                "pct_chg": row.get("涨跌幅"),
                "trade_date": datetime.now().strftime('%Y-%m-%d')
            })
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Get quotes failed for {symbol}: {e}")
            # 如果实时行情失败，尝试用历史数据作为后备
            try:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                df = await asyncio.to_thread(
                    _akshare_call,
                    ak.stock_zh_a_hist,
                    retries=2,
                    delay=1,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=""
                )
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    self.logger.info(f"Using historical data as fallback for {symbol}")
                    result = self.standardize_quotes({
                        "symbol": symbol,
                        "name": symbol,
                        "close": latest.get("收盘"),
                        "open": latest.get("开盘"),
                        "high": latest.get("最高"),
                        "low": latest.get("最低"),
                        "pre_close": latest.get("收盘"),
                        "volume": latest.get("成交量"),
                        "amount": latest.get("成交额"),
                        "change": latest.get("涨跌幅"),
                        "pct_chg": latest.get("涨跌幅"),
                        "trade_date": str(latest.get("日期"))[:10] if latest.get("日期") else ""
                    })
                    self._set_cache(cache_key, result)
                    return result
            except Exception as e2:
                self.logger.error(f"Fallback also failed: {e2}")
            return None
    
    async def get_historical(
        self,
        symbol: str,
        start_date: Union[str, date],
        end_date: Union[str, date] = None,
        period: str = "daily"
    ) -> Optional[pd.DataFrame]:
        """获取历史数据 - 使用重试机制"""
        if not self.is_available():
            return None
        
        try:
            start_str = self._format_date(start_date)
            end_str = self._format_date(end_date) if end_date else datetime.now().strftime('%Y%m%d')
            
            # 构建参数
            params = {
                "symbol": symbol,
                "start_date": start_str.replace('-', ''),
                "end_date": end_str.replace('-', ''),
                "adjust": "qfq"
            }
            if period == "weekly":
                params["period"] = "weekly"
            elif period == "monthly":
                params["period"] = "monthly"
            
            df = await asyncio.to_thread(
                _akshare_call,
                ak.stock_zh_a_hist,
                retries=3,
                delay=2,
                **params
            )
            
            if df is not None and not df.empty:
                self.logger.info(f"Got {len(df)} historical records for {symbol}")
                return df
            
            return None
            
        except Exception as e:
            self.logger.error(f"Get historical failed for {symbol}: {e}")
            return None
    
    async def get_stock_list(self, market: str = None) -> Optional[List[Dict[str, Any]]]:
        """获取股票列表"""
        if not self.is_available():
            return None
        
        try:
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            
            if df is None or df.empty:
                return None
            
            stock_list = []
            for _, row in df.iterrows():
                stock_list.append({
                    "symbol": row.get("代码", ""),
                    "name": row.get("名称", ""),
                    "current_price": row.get("最新价"),
                    "change_pct": row.get("涨跌幅"),
                    "volume": row.get("成交量"),
                    "data_source": "akshare"
                })
            
            return stock_list
            
        except Exception as e:
            self.logger.error(f"Get stock list failed: {e}")
            return None
    
    async def get_news(self, symbol: str = None, hours_back: int = 24, max_news: int = 10) -> Optional[List[Dict[str, Any]]]:
        """获取股票新闻"""
        if not self.is_available():
            return None
        
        try:
            clean_symbol = symbol.replace('.SH', '').replace('.SZ', '').replace('.HK', '') if symbol else None
            
            if clean_symbol:
                df = await asyncio.to_thread(ak.stock_news_em, symbol=clean_symbol)
            else:
                df = await asyncio.to_thread(ak.stock_news_em, symbol="000001")
            
            if df is None or df.empty:
                return []
            
            news_list = []
            for _, row in df.head(max_news).iterrows():
                news_item = {
                    "title": str(row.get("新闻标题", "")),
                    "content": str(row.get("新闻内容", "")),
                    "source": "东方财富",
                    "publish_time": row.get("发布时间", ""),
                    "url": row.get("新闻链接", ""),
                    "data_source": "akshare"
                }
                news_list.append(news_item)
            
            return news_list
            
        except Exception as e:
            self.logger.error(f"Get news failed: {e}")
            return None

    async def get_stock_basic(self, symbol: str = None) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """获取股票基础信息"""
        if not AKSHARE_AVAILABLE:
            return None
        
        try:
            if symbol:
                clean_symbol = symbol.replace('.SH', '').replace('.SZ', '').replace('.HK', '')
                df = await asyncio.to_thread(
                    _akshare_call,
                    ak.stock_individual_info_em,
                    symbol=clean_symbol,
                    retries=2
                )
                if df is None or df.empty:
                    return None
                return df.to_dict('records')[0] if hasattr(df, 'to_dict') else dict(df.iloc[0])
            else:
                df = await asyncio.to_thread(
                    _akshare_call,
                    ak.stock_zh_a_spot_em,
                    retries=2
                )
                if df is None or df.empty:
                    return None
                return df.head(100).to_dict('records')
        except Exception as e:
            self.logger.error(f"Get stock basic failed: {e}")
            return None
