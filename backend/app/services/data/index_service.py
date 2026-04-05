"""
指数数据服务
提供指数行情、历史数据等服务
"""
import logging
from typing import Optional, Dict, Any
import pandas as pd

from .akshare_client import get_akshare_client
from .tushare_client import get_tushare_client
from app.services.logging_manager import get_logger

logger = get_logger("data.index_service")


INDEX_CODES = {
    "000001": "上证指数",
    "399001": "深证成指",
    "399006": "创业板指",
    "000300": "沪深300",
    "000016": "上证50",
    "000905": "中证500",
    "000852": "中证1000",
    "399300": "沪深300(深市)",
    "000688": "科创50",
    "399108": "深证100R",
}


class IndexService:
    """指数数据服务类"""
    
    def __init__(self):
        self.akshare = get_akshare_client()
        self.tushare = get_tushare_client()
    
    def get_quote(self, index_code: str) -> Optional[Dict[str, Any]]:
        """
        获取指数实时行情
        
        Args:
            index_code: 指数代码
            
        Returns:
            行情字典
        """
        if self.akshare.is_available:
            spot = self.akshare.get_index_realtime()
            if spot is not None:
                for code in [index_code, f"sh{index_code}", f"sz{index_code}"]:
                    result = spot[spot['代码'] == code]
                    if not result.empty:
                        return result.iloc[0].to_dict()
        return None
    
    def get_daily(self, index_code: str, start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        """
        获取指数日线数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame
        """
        if not start_date:
            from datetime import datetime, timedelta
            end = datetime.now()
            start = end - timedelta(days=365)
            start_date = start.strftime("%Y%m%d")
            end_date = end.strftime("%Y%m%d")
        
        if self.akshare.is_available:
            return self.akshare.get_index_daily(index_code)
        
        if self.tushare.is_connected:
            ts_code = f"{index_code}.SH" if index_code.startswith('0') else f"{index_code}.SZ"
            return self.tushare.get_zz_index_daily(ts_code, start_date, end_date)
        
        return None
    
    def get_realtime_all(self) -> Optional[pd.DataFrame]:
        """
        获取所有指数实时行情
        
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            return self.akshare.get_index_realtime()
        return None
    
    def get_weight(self, index_code: str) -> Optional[pd.DataFrame]:
        """
        获取指数成分股权重
        
        Args:
            index_code: 指数代码
            
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            code = f"{index_code}.SH" if index_code.startswith('0') else f"{index_code}.SZ"
            return self.akshare.get_index_weight(code)
        return None
    
    def format_quote(self, quote: Dict[str, Any], index_name: str = "") -> str:
        """
        格式化指数行情
        
        Args:
            quote: 行情字典
            index_name: 指数名称
            
        Returns:
            格式化的字符串
        """
        if not quote:
            return "无数据"
        
        try:
            return f"""
{index_name}
代码: {quote.get('代码', quote.get('ts_code', 'N/A'))}
当前点位: {quote.get('最新价', 'N/A')}
涨跌幅: {quote.get('涨跌幅', 'N/A')}%
涨跌额: {quote.get('涨跌额', 'N/A')}
成交量: {quote.get('成交量', 'N/A')}
成交额: {quote.get('成交额', 'N/A')}
最高: {quote.get('最高', 'N/A')}
最低: {quote.get('最低', 'N/A')}
今开: {quote.get('今开', 'N/A')}
昨收: {quote.get('昨收', 'N/A')}
"""
        except Exception as e:
            logger.error(f"格式化指数行情失败: {e}")
            return str(quote)
    
    def format_daily(self, df: pd.DataFrame, limit: int = 30) -> str:
        """
        格式化指数日线数据
        
        Args:
            df: 日线数据
            limit: 显示行数
            
        Returns:
            格式化的字符串
        """
        if df is None or df.empty:
            return "无数据"
        
        df = df.tail(limit)
        
        lines = ["日期\t\t开盘\t收盘\t涨跌幅\t成交量"]
        
        for _, row in df.iterrows():
            date = row.get('date', '')
            if isinstance(date, str) and len(date) >= 10:
                date = date[:10]
            
            open_p = row.get('open', 0)
            close = row.get('close', 0)
            pct = row.get('pct_chg', row.get('涨跌幅', 0))
            vol = row.get('volume', row.get('vol', 0))
            
            lines.append(f"{date}\t{open_p:.2f}\t{close:.2f}\t{pct:.2f}%\t{vol:.0f}")
        
        return "\n".join(lines)
    
    def get_index_list(self) -> Dict[str, str]:
        """
        获取常用指数列表
        
        Returns:
            指数代码到名称的字典
        """
        return INDEX_CODES.copy()


_index_service: Optional[IndexService] = None


def get_index_service() -> IndexService:
    """获取指数服务单例"""
    global _index_service
    if _index_service is None:
        _index_service = IndexService()
    return _index_service
