"""
BaoStock 数据提供者 - A股/港股历史数据
"""
import asyncio
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date
import logging

from .base import BaseStockProvider
from app.services.logging_manager import get_logger

logger = get_logger("stock_data.baostock")

BAOSTOCK_AVAILABLE = False
try:
    import baostock as bs
    BAOSTOCK_AVAILABLE = True
except ImportError:
    bs = None


class BaoStockProvider(BaseStockProvider):
    """BaoStock 股票数据提供者"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("BaoStock")
        self.config = config or {}
    
    async def connect(self) -> bool:
        """连接到 BaoStock"""
        if not BAOSTOCK_AVAILABLE:
            self.logger.error("BaoStock library not installed")
            return False
        
        try:
            lg = bs.login()
            if lg.error_code == '0':
                self.connected = True
                self.logger.info("BaoStock connected successfully")
                return True
            self.logger.error(f"BaoStock login failed: {lg.error_msg}")
            return False
        except Exception as e:
            self.logger.error(f"BaoStock connection failed: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if BAOSTOCK_AVAILABLE:
            bs.logout()
        self.connected = False
    
    def is_available(self) -> bool:
        return BAOSTOCK_AVAILABLE and self.connected
    
    async def get_stock_basic(self, symbol: str = None) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """获取股票基础信息"""
        if not self.is_available():
            return None
        
        try:
            if symbol:
                rs = bs.query_stock_basic(code=symbol)
            else:
                rs = bs.query_all_stock()
            
            stock_list = []
            while rs.error_code == '0' and rs.next():
                stock_data = rs.get_row_data()
                stock_list.append({
                    "symbol": stock_data[0],
                    "name": stock_data[1],
                    "date": stock_data[2],
                    "data_source": "baostock"
                })
            
            if symbol:
                return stock_list[0] if stock_list else None
            return stock_list
            
        except Exception as e:
            self.logger.error(f"Get stock basic failed: {e}")
            return None
    
    async def get_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情 - BaoStock 主要支持历史数据"""
        if not self.is_available():
            return None
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            rs = bs.query_history_k_data_plus(
                symbol,
                "date,code,open,high,low,close,volume,amount,turn",
                start_date=today,
                end_date=today,
                frequency="d"
            )
            
            if rs.error_code == '0' and rs.next():
                data = rs.get_row_data()
                return self.standardize_quotes({
                    "symbol": symbol,
                    "date": data[0],
                    "open": data[2],
                    "high": data[3],
                    "low": data[4],
                    "close": data[5],
                    "volume": data[6],
                    "amount": data[7],
                    "trade_date": data[0]
                })
            
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
    ) -> Optional[Any]:
        """获取历史数据"""
        if not self.is_available():
            return None
        
        try:
            start_str = self._format_date(start_date)
            end_str = self._format_date(end_date) if end_date else datetime.now().strftime('%Y-%m-%d')
            
            frequency = "d" if period == "daily" else "w" if period == "weekly" else "m"
            
            rs = bs.query_history_k_data_plus(
                symbol,
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=start_str,
                end_date=end_str,
                frequency=frequency,
                adjustflag="2"
            )
            
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())
            
            if data_list:
                import pandas as pd
                df = pd.DataFrame(data_list, columns=[
                    "date", "code", "open", "high", "low", "close", 
                    "volume", "amount", "turn", "pctChg"
                ])
                self.logger.info(f"Got {len(df)} historical records for {symbol}")
                return df
            
            return None
            
        except Exception as e:
            self.logger.error(f"Get historical failed: {e}")
            return None
    
    async def get_stock_list(self, market: str = None) -> Optional[List[Dict[str, Any]]]:
        """获取股票列表"""
        return await self.get_stock_basic()

    def _to_baostock_code(self, symbol: str) -> str:
        """转换为BaoStock代码格式"""
        s = str(symbol).strip().upper()
        if s.endswith('.SH') or s.endswith('.SZ'):
            code, exch = s.split('.')
            prefix = 'sh' if exch == 'SH' else 'sz'
            return f"{prefix}.{code}"
        if len(s) >= 6 and s[0] == '6':
            return f"sh.{s[:6]}"
        return f"sz.{s[:6]}"

    def _determine_market(self, code: str) -> str:
        """确定股票所属市场"""
        code = str(code).strip()
        if code.startswith('6'):
            return "上海证券交易所"
        elif code.startswith('0') or code.startswith('3'):
            return "深圳证券交易所"
        elif code.startswith('8'):
            return "北京证券交易所"
        return "未知市场"

    async def get_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票详细信息"""
        if not self.is_available():
            return None
        
        try:
            bs_code = self._to_baostock_code(symbol)
            
            rs = bs.query_stock_basic(code=bs_code)
            if rs.error_code != '0':
                self.logger.error(f"Query stock basic failed: {rs.error_msg}")
                return None
            
            data = None
            while rs.error_code == '0' and rs.next():
                data = rs.get_row_data()
                break
            
            if not data:
                return None
            
            return {
                "symbol": symbol,
                "code": data[0],
                "name": data[1],
                "date": data[2],
                "market": self._determine_market(symbol),
                "exchange": "SSE" if symbol.startswith('6') else ("SZSE" if symbol.startswith(('0', '3')) else "BSE"),
                "data_source": "baostock"
            }
        except Exception as e:
            self.logger.error(f"Get stock basic info failed: {e}")
            return None

    async def get_valuation_data(self, symbol: str, trade_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取估值数据（PE、PB等）"""
        if not self.is_available():
            return None
        
        try:
            bs_code = self._to_baostock_code(symbol)
            
            if not trade_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - __import__('datetime').timedelta(days=30)).strftime('%Y-%m-%d')
            else:
                start_date = trade_date
                end_date = trade_date
            
            rs = bs.query_history_k_data_plus(
                code=bs_code,
                fields="date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"
            )
            
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return None
            
            latest = data_list[-1]
            return {
                "symbol": symbol,
                "trade_date": latest[0],
                "close": self._safe_float(latest[2]),
                "pe_ttm": self._safe_float(latest[3]),
                "pb_mrq": self._safe_float(latest[4]),
                "ps_ttm": self._safe_float(latest[5]),
                "pcf_ncf_ttm": self._safe_float(latest[6]),
                "data_source": "baostock",
                "data_date": f"数据最新至 {latest[0]}（系统自动获取最近可用数据）"
            }
        except Exception as e:
            self.logger.error(f"Get valuation data failed: {e}")
            return None

    async def get_financial_data(self, symbol: str, year: Optional[int] = None, quarter: int = 4) -> Optional[Dict[str, Any]]:
        """获取财务数据"""
        if not self.is_available():
            return None
        
        try:
            bs_code = self._to_baostock_code(symbol)
            if not year:
                year = datetime.now().year - 1
            
            rs = bs.query_profit_data(code=bs_code, year=year, quarter=quarter)
            
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return {"symbol": symbol, "year": year, "quarter": quarter, "message": "No data available"}
            
            data = data_list[0]
            return {
                "symbol": symbol,
                "year": year,
                "quarter": quarter,
                "net_profit": self._safe_float(data[2]) if len(data) > 2 else None,
                "net_profit_yoy": self._safe_float(data[3]) if len(data) > 3 else None,
                "gross_profit_margin": self._safe_float(data[4]) if len(data) > 4 else None,
                "net_profit_margin": self._safe_float(data[5]) if len(data) > 5 else None,
                "roe": self._safe_float(data[6]) if len(data) > 6 else None,
                "data_source": "baostock"
            }
        except Exception as e:
            self.logger.error(f"Get financial data failed: {e}")
            return None

    def _safe_float(self, value: Any) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None or value == "" or value == "-":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
