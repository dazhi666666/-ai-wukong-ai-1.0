"""
股票数据服务
提供股票行情、历史数据等服务
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd

from .tushare_client import get_tushare_client
from .akshare_client import get_akshare_client
from app.services.logging_manager import get_logger

logger = get_logger("data.stock_service")


class StockService:
    """股票数据服务类"""
    
    def __init__(self):
        self.tushare = get_tushare_client()
        self.akshare = get_akshare_client()
    
    def normalize_code(self, stock_code: str) -> str:
        """
        标准化股票代码
        
        Args:
            stock_code: 股票代码
            
        Returns:
            标准化后的代码
        """
        stock_code = stock_code.strip().upper()
        
        for suffix in ['.SH', '.SZ', '.XSHG', '.XSGE']:
            stock_code = stock_code.replace(suffix, '')
        
        if stock_code.startswith('6') or stock_code.startswith('9'):
            return f"{stock_code}.SH"
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            return f"{stock_code}.SZ"
        elif stock_code.startswith('8') or stock_code.startswith('4'):
            return f"{stock_code}.BJ"
        else:
            return f"{stock_code}.SZ"
    
    def get_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票实时行情
        
        Args:
            stock_code: 股票代码
            
        Returns:
            行情字典
        """
        ts_code = self.normalize_code(stock_code)
        
        if self.tushare.is_connected:
            return self.tushare.get_realtime_quote(ts_code)
        
        if self.akshare.is_available:
            symbol = ts_code.split('.')[0]
            return self.akshare.get_stock_realtime(symbol)
        
        return None
    
    def get_quotes_batch(self, stock_codes: List[str]) -> Optional[pd.DataFrame]:
        """
        批量获取股票行情
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            DataFrame
        """
        normalized_codes = [self.normalize_code(code) for code in stock_codes]
        
        if self.tushare.is_connected:
            ts_codes = [c.replace('.', '').lower() for c in normalized_codes]
            return self.tushare.get_realtime_quotes_batch(ts_codes)
        
        if self.akshare.is_available:
            symbols = [c.split('.')[0] for c in normalized_codes]
            return self.akshare.get_stock_realtime_batch(symbols)
        
        return None
    
    def get_daily(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取股票日线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame
        """
        ts_code = self.normalize_code(stock_code)
        
        if self.tushare.is_connected:
            df = self.tushare.get_stock_daily(ts_code, start_date, end_date)
            if df is not None:
                df = df.sort_values('trade_date')
            return df
        
        if self.akshare.is_available:
            symbol = ts_code.split('.')[0]
            return self.akshare.get_stock_daily(symbol, start_date, end_date)
        
        return None
    
    def get_minute(self, stock_code: str, start_time: str, end_time: str, freq: str = "5") -> Optional[pd.DataFrame]:
        """
        获取股票分钟线数据
        
        Args:
            stock_code: 股票代码
            start_time: 开始时间
            end_time: 结束时间
            freq: 频率 (1/5/15/30/60)
            
        Returns:
            DataFrame
        """
        ts_code = self.normalize_code(stock_code)
        
        if self.tushare.is_connected:
            return self.tushare.get_stock_minute(ts_code, start_time, end_time, freq)
        
        return None
    
    def get_kline(self, stock_code: str, adjust: str = "qfq") -> Optional[pd.DataFrame]:
        """
        获取股票K线数据
        
        Args:
            stock_code: 股票代码
            adjust: 复权类型
            
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            symbol = stock_code.split('.')[0]
            return self.akshare.get_stock_kline(symbol, adjust)
        return None
    
    def get_basic(self, exchange: str = "") -> Optional[pd.DataFrame]:
        """
        获取股票基本信息
        
        Args:
            exchange: 交易所
            
        Returns:
            DataFrame
        """
        if self.tushare.is_connected:
            return self.tushare.get_stock_basic(exchange)
        return None
    
    def get_daily_basic(self, trade_date: str) -> Optional[pd.DataFrame]:
        """
        获取每日交易统计
        
        Args:
            trade_date: 交易日期
            
        Returns:
            DataFrame
        """
        if self.tushare.is_connected:
            return self.tushare.get_daily_basic(trade_date)
        return None
    
    def format_quote(self, quote: Dict[str, Any]) -> str:
        """
        格式化行情为字符串
        
        Args:
            quote: 行情字典
            
        Returns:
            格式化的字符串
        """
        if not quote:
            return "无数据"
        
        try:
            return f"""
股票代码: {quote.get('ts_code', 'N/A')}
当前价格: {quote.get('price', quote.get('last_price', 'N/A'))}
涨跌幅: {quote.get('pct_chg', 'N/A')}%
成交量: {quote.get('vol', 'N/A')}
成交额: {quote.get('amount', 'N/A')}
最高: {quote.get('high', 'N/A')}
最低: {quote.get('low', 'N/A')}
开盘: {quote.get('open', 'N/A')}
昨收: {quote.get('pre_close', 'N/A')}
"""
        except Exception as e:
            logger.error(f"格式化行情失败: {e}")
            return str(quote)
    
    def format_daily(self, df: pd.DataFrame, limit: int = 30) -> str:
        """
        格式化日线数据为字符串
        
        Args:
            df: 日线数据
            limit: 显示行数
            
        Returns:
            格式化的字符串
        """
        if df is None or df.empty:
            return "无数据"
        
        df = df.tail(limit)
        
        lines = ["日期\t\t开盘\t收盘\t涨跌幅\t成交量\t成交额"]
        
        for _, row in df.iterrows():
            date = row.get('trade_date', '')
            if isinstance(date, str) and len(date) == 8:
                date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
            
            open_p = row.get('open', 0)
            close = row.get('close', 0)
            pct = row.get('pct_chg', 0)
            vol = row.get('vol', 0)
            amount = row.get('amount', 0)
            
            lines.append(f"{date}\t{open_p:.2f}\t{close:.2f}\t{pct:.2f}%\t{vol:.0f}\t{amount:.2f}")
        
        return "\n".join(lines)
    
    def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票完整信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            包含多种数据的字典
        """
        result = {
            "code": stock_code,
            "normalized_code": self.normalize_code(stock_code),
            "quote": self.get_quote(stock_code),
            "basic": None,
        }
        
        if self.tushare.is_connected:
            ts_code = self.normalize_code(stock_code)
            basic = self.tushare.get_stock_basic()
            if basic is not None:
                result["basic"] = basic[basic['ts_code'] == ts_code].to_dict('records')
        
        return result


_stock_service: Optional[StockService] = None


def get_stock_service() -> StockService:
    """获取股票服务单例"""
    global _stock_service
    if _stock_service is None:
        _stock_service = StockService()
    return _stock_service
