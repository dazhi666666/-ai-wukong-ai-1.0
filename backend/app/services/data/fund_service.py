"""
基金数据服务
提供基金行情、净值、持仓等服务
"""
import logging
from typing import Optional, Dict, Any
import pandas as pd

from .akshare_client import get_akshare_client
from .tushare_client import get_tushare_client
from app.services.logging_manager import get_logger

logger = get_logger("data.fund_service")


class FundService:
    """基金数据服务类"""
    
    def __init__(self):
        self.akshare = get_akshare_client()
        self.tushare = get_tushare_client()
    
    def get_etf_spot(self) -> Optional[pd.DataFrame]:
        """
        获取 ETF 实时行情
        
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            return self.akshare.get_fund_etf_spot()
        return None
    
    def get_lof_spot(self) -> Optional[pd.DataFrame]:
        """
        获取 LOF 实时行情
        
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            return self.akshare.get_fund_lof_spot()
        return None
    
    def get_etf_hist(self, symbol: str, period: str = "daily") -> Optional[pd.DataFrame]:
        """
        获取 ETF 历史数据
        
        Args:
            symbol: ETF 代码
            period: 周期
            
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            return self.akshare.get_fund_etf_hist(symbol, period)
        return None
    
    def get_nav(self, fund_code: str) -> Optional[pd.DataFrame]:
        """
        获取基金净值
        
        Args:
            fund_code: 基金代码
            
        Returns:
            DataFrame
        """
        if self.tushare.is_connected:
            return self.tushare.get_fund_nav(fund_code)
        return None
    
    def get_basic(self, market: str = "E") -> Optional[pd.DataFrame]:
        """
        获取基金基本信息
        
        Args:
            market: 市场类型
            
        Returns:
            DataFrame
        """
        if self.tushare.is_connected:
            return self.tushare.get_fund_basic(market)
        return None
    
    def get_portfolio(self, fund_code: str) -> Optional[pd.DataFrame]:
        """
        获取基金持仓
        
        Args:
            fund_code: 基金代码
            
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            return self.akshare.get_fund_portfolio(fund_code)
        return None
    
    def get_spot_all(self) -> Optional[pd.DataFrame]:
        """
        获取所有基金实时行情
        
        Returns:
            DataFrame
        """
        etf = self.get_etf_spot()
        lof = self.get_lof_spot()
        
        if etf is not None and lof is not None:
            return pd.concat([etf, lof], ignore_index=True)
        elif etf is not None:
            return etf
        elif lof is not None:
            return lof
        return None
    
    def format_etf_spot(self, df: pd.DataFrame, limit: int = 20) -> str:
        """
        格式化 ETF 行情
        
        Args:
            df: 行情数据
            limit: 显示数量
            
        Returns:
            格式化字符串
        """
        if df is None or df.empty:
            return "无数据"
        
        df = df.head(limit)
        
        lines = ["代码\t名称\t最新价\t涨跌幅\t成交量"]
        
        for _, row in df.iterrows():
            code = row.get('代码', '')
            name = row.get('名称', '')
            price = row.get('最新价', 0)
            pct = row.get('涨跌幅', 0)
            vol = row.get('成交量', 0)
            
            lines.append(f"{code}\t{name}\t{price:.2f}\t{pct:.2f}%\t{vol:.0f}")
        
        return "\n".join(lines)


_fund_service: Optional[FundService] = None


def get_fund_service() -> FundService:
    """获取基金服务单例"""
    global _fund_service
    if _fund_service is None:
        _fund_service = FundService()
    return _fund_service
