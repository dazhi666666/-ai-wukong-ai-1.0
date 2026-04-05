"""
Tushare 数据提供者 - A股数据
"""
import os
import asyncio
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date, timedelta
import pandas as pd
import logging

from .base import BaseStockProvider
from app.services.logging_manager import get_logger

logger = get_logger("stock_data.tushare")

TUSHARE_AVAILABLE = False
try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    ts = None


class TushareProvider(BaseStockProvider):
    """Tushare 股票数据提供者"""
    
    def __init__(self, token: str = None, config: Dict[str, Any] = None):
        super().__init__("Tushare")
        self.api = None
        self.token = token or os.getenv("TUSHARE_TOKEN", "")
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30)
        self.max_retries = self.config.get("max_retries", 3)
    
    async def connect(self) -> bool:
        """连接到 Tushare"""
        if not TUSHARE_AVAILABLE:
            self.logger.error("Tushare library not installed")
            return False
        
        if not self.token:
            self.logger.error("Tushare token not configured")
            return False
        
        try:
            ts.set_token(self.token)
            self.api = ts.pro_api()
            
            test_data = await asyncio.to_thread(
                self.api.stock_basic,
                list_status='L',
                limit=1
            )
            
            if test_data is not None and not test_data.empty:
                self.connected = True
                self.logger.info("Tushare connected successfully")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Tushare connection failed: {e}")
            return False
    
    def is_available(self) -> bool:
        return TUSHARE_AVAILABLE and self.connected and self.api is not None
    
    async def get_stock_basic(self, symbol: str = None) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """获取股票基础信息"""
        if not self.is_available():
            return None
        
        try:
            ts_code = self._normalize_ts_code(symbol) if symbol else None
            
            df = await asyncio.to_thread(
                self.api.stock_basic,
                ts_code=ts_code,
                fields='ts_code,symbol,name,area,industry,market,exchange,list_date,is_hs'
            )
            
            if df is None or df.empty:
                return None
            
            if symbol:
                return self.standardize_basic_info(df.iloc[0].to_dict())
            
            stock_list = []
            for _, row in df.iterrows():
                stock_list.append(self.standardize_basic_info(row.to_dict()))
            return stock_list
            
        except Exception as e:
            self.logger.error(f"Get stock basic failed: {e}")
            return None
    
    async def get_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情"""
        if not self.is_available():
            return None
        
        try:
            ts_code = self._normalize_ts_code(symbol)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=3)).strftime('%Y%m%d')
            
            df = await asyncio.to_thread(
                self.api.daily,
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and not df.empty:
                row = df.iloc[0].to_dict()
                quote_data = {
                    'ts_code': row.get('ts_code'),
                    'symbol': symbol,
                    'trade_date': row.get('trade_date'),
                    'open': row.get('open'),
                    'high': row.get('high'),
                    'low': row.get('low'),
                    'close': row.get('close'),
                    'pre_close': row.get('pre_close'),
                    'change': row.get('change'),
                    'pct_chg': row.get('pct_chg'),
                    'volume': row.get('vol') * 100,
                    'amount': row.get('amount') * 1000,
                }
                return self.standardize_quotes(quote_data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Get quotes failed: {e}")
            return None
    
    async def get_historical(
        self,
        symbol: str,
        start_date: Union[str, date],
        end_date: Union[str, date] = None,
        period: str = "daily"
    ) -> Optional[pd.DataFrame]:
        """获取历史数据"""
        if not self.is_available():
            return None
        
        try:
            ts_code = self._normalize_ts_code(symbol)
            start_str = self._format_date(start_date)
            end_str = self._format_date(end_date) if end_date else datetime.now().strftime('%Y%m%d')
            
            freq_map = {"daily": "D", "weekly": "W", "monthly": "M"}
            freq = freq_map.get(period, "D")
            
            df = await asyncio.to_thread(
                ts.pro_bar,
                ts_code=ts_code,
                api=self.api,
                start_date=start_str,
                end_date=end_str,
                freq=freq,
                adj='qfq'
            )
            
            if df is not None and not df.empty:
                self.logger.info(f"Got {len(df)} historical records for {symbol}")
                return df
            
            return None
            
        except Exception as e:
            self.logger.error(f"Get historical failed: {e}")
            return None
    
    async def get_stock_list(self, market: str = None) -> Optional[List[Dict[str, Any]]]:
        """获取股票列表"""
        if not self.is_available():
            return None
        
        try:
            params = {
                'list_status': 'L',
                'fields': 'ts_code,symbol,name,area,industry,market,exchange,list_date,is_hs'
            }
            
            if market == "CN":
                params['exchange'] = 'SSE,SZSE'
            
            df = await asyncio.to_thread(self.api.stock_basic, **params)
            
            if df is None or df.empty:
                return None
            
            stock_list = []
            for _, row in df.iterrows():
                stock_list.append(self.standardize_basic_info(row.to_dict()))
            
            self.logger.info(f"Got {len(stock_list)} stocks")
            return stock_list
            
        except Exception as e:
            self.logger.error(f"Get stock list failed: {e}")
            return None
    
    async def get_financial(self, symbol: str, limit: int = 4) -> Optional[Dict[str, Any]]:
        """获取财务数据"""
        if not self.is_available():
            return None
        
        try:
            ts_code = self._normalize_ts_code(symbol)
            
            financial_data = {}
            
            try:
                indicator_df = await asyncio.to_thread(
                    self.api.fina_indicator,
                    ts_code=ts_code,
                    limit=limit
                )
                if indicator_df is not None and not indicator_df.empty:
                    financial_data['indicators'] = indicator_df.to_dict('records')
            except Exception as e:
                self.logger.warning(f"Get financial indicators failed: {e}")
            
            if financial_data:
                return {
                    "symbol": symbol,
                    "ts_code": ts_code,
                    "data": financial_data,
                    "data_source": "tushare",
                    "updated_at": datetime.utcnow().isoformat()
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Get financial failed: {e}")
            return None
    
    async def get_news(self, symbol: str = None, hours_back: int = 24, max_news: int = 10) -> Optional[List[Dict[str, Any]]]:
        """获取股票新闻"""
        if not self.is_available():
            return None
        
        try:
            from datetime import datetime, timedelta
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            start_date = start_time.strftime('%Y-%m-%d %H:%M:%S')
            end_date = end_time.strftime('%Y-%m-%d %H:%M:%S')
            
            sources = ['sina', 'eastmoney', '10jqka']
            all_news = []
            
            for source in sources:
                try:
                    news_df = await asyncio.to_thread(
                        self.api.news,
                        src=source,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if news_df is not None and not news_df.empty:
                        for _, row in news_df.head(max_news).iterrows():
                            news_item = {
                                "title": str(row.get('title', '')),
                                "content": str(row.get('content', '')),
                                "source": source,
                                "publish_time": row.get('datetime', ''),
                                "url": "",
                                "data_source": "tushare"
                            }
                            all_news.append(news_item)
                            
                except Exception:
                    continue
                
                if len(all_news) >= max_news:
                    break
            
            return all_news[:max_news] if all_news else []
            
        except Exception as e:
            self.logger.error(f"Get news failed: {e}")
            return None
    
    def _normalize_ts_code(self, symbol: str) -> str:
        """标准化为 Tushare ts_code 格式"""
        if '.' in symbol:
            return symbol
        
        if symbol.isdigit() and len(symbol) == 6:
            if symbol.startswith(('60', '68', '90')):
                return f"{symbol}.SH"
            else:
                return f"{symbol}.SZ"
        
        return symbol
