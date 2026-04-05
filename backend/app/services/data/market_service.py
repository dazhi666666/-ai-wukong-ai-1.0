"""
特色数据服务
提供资金流向、融资融券、龙虎榜等特色数据
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from .tushare_client import get_tushare_client
from .akshare_client import get_akshare_client
from .stock_service import get_stock_service
from app.services.logging_manager import get_logger

logger = get_logger("data.market_service")


class MarketService:
    """特色市场数据服务类"""
    
    def __init__(self):
        self.tushare = get_tushare_client()
        self.akshare = get_akshare_client()
        self.stock = get_stock_service()
    
    def get_moneyflow(self, stock_code: str, days: int = 10) -> Optional[pd.DataFrame]:
        """
        获取资金流向
        
        Args:
            stock_code: 股票代码
            days: 天数
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days+30)).strftime("%Y%m%d")
        
        return self.tushare.get_moneyflow(ts_code, start_date, end_date)
    
    def get_margin(self, stock_code: str, days: int = 10) -> Optional[pd.DataFrame]:
        """
        获取融资融券数据
        
        Args:
            stock_code: 股票代码
            days: 天数
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        return self.tushare.get_margin(ts_code, start_date, end_date)
    
    def get_leaderboard(self, date: str = "") -> Optional[pd.DataFrame]:
        """
        获取龙虎榜
        
        Args:
            date: 日期 (YYYYMMDD)，默认最新
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        return self.tushare.get_top_list(date)
    
    def get_leaderboard_detail(self, date: str = "") -> Optional[pd.DataFrame]:
        """
        获取龙虎榜机构明细
        
        Args:
            date: 日期
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        return self.tushare.get_top_inst(date)
    
    def get_restrained_stock(self, stock_code: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        获取限售股解禁
        
        Args:
            stock_code: 股票代码
            days: 天数
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        return self.tushare.get_stk_holdertrade(ts_code, start_date, end_date)
    
    def get_moneyflow_hsgt(self) -> Optional[pd.DataFrame]:
        """
        获取北向资金流向
        
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            return self.akshare.get_moneyflow_hsgt()
        return None
    
    def get_market_flow(self) -> Optional[pd.DataFrame]:
        """
        获取市场资金流向
        
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            return self.akshare.get_stock_market_fund_flow()
        return None
    
    def get_stock_individual_flow(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取个股资金流向
        
        Args:
            stock_code: 股票代码
            
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            symbol = stock_code.split('.')[0]
            return self.akshare.get_stock_individual_flow(symbol)
        return None
    
    def get_industry_flow(self, n: int = 10) -> Optional[pd.DataFrame]:
        """
        获取行业资金流向
        
        Args:
            n: 返回数量
            
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            return self.akshare.get_stock_fund_flow_industry(n)
        return None
    
    def get_concept_flow(self, n: int = 10) -> Optional[pd.DataFrame]:
        """
        获取概念资金流向
        
        Args:
            n: 返回数量
            
        Returns:
            DataFrame
        """
        if self.akshare.is_available:
            return self.akshare.get_stock_fund_flow_concept(n)
        return None
    
    def get_limit_up_pool(self, date: str = "") -> Optional[pd.DataFrame]:
        """
        获取涨停板池
        
        Args:
            date: 日期
            
        Returns:
            DataFrame
        """
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        if self.akshare.is_available:
            return self.akshare.get_stock_zt_pool(date)
        return None
    
    def get_limit_strong(self, date: str = "") -> Optional[pd.DataFrame]:
        """
        获取强势股池
        
        Args:
            date: 日期
            
        Returns:
            DataFrame
        """
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        if self.akshare.is_available:
            return self.akshare.get_stock_zt_pool_strong(date)
        return None
    
    def format_moneyflow(self, df: pd.DataFrame) -> str:
        """
        格式化资金流向
        
        Args:
            df: 资金流向数据
            
        Returns:
            格式化字符串
        """
        if df is None or df.empty:
            return "无数据"
        
        df = df.head(5)
        
        lines = ["日期\t\t主力净流入\t超大单净流入\t大单净流入\t中单净流入\t小单净流入"]
        
        for _, row in df.iterrows():
            date = row.get('trade_date', '')
            if isinstance(date, str) and len(date) == 8:
                date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
            
            main = row.get('net_main', 0) or 0
            super_large = row.get('net_super_large', 0) or 0
            large = row.get('net_large', 0) or 0
            medium = row.get('net_medium', 0) or 0
            small = row.get('net_small', 0) or 0
            
            lines.append(f"{date}\t{main:.2f}\t{super_large:.2f}\t{large:.2f}\t{medium:.2f}\t{small:.2f}")
        
        return "\n".join(lines)
    
    def format_margin(self, df: pd.DataFrame) -> str:
        """
        格式化融资融券
        
        Args:
            df: 融资融券数据
            
        Returns:
            格式化字符串
        """
        if df is None or df.empty:
            return "无数据"
        
        df = df.head(5)
        
        lines = ["日期\t\t融资余额\t融资买入\t融资偿还\t融券余额\t融券卖出"]
        
        for _, row in df.iterrows():
            date = row.get('trade_date', '')
            if isinstance(date, str) and len(date) == 8:
                date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
            
            rzye = row.get('rzye', 0) or 0
            rzmre = row.get('rzmre', 0) or 0
            rzche = row.get('rzche', 0) or 0
            rqye = row.get('rqye', 0) or 0
            rqmcl = row.get('rqmcl', 0) or 0
            
            lines.append(f"{date}\t{rzye:.2f}\t{rzmre:.2f}\t{rzche:.2f}\t{rqye:.2f}\t{rqmcl:.2f}")
        
        return "\n".join(lines)
    
    def format_leaderboard(self, df: pd.DataFrame) -> str:
        """
        格式化龙虎榜
        
        Args:
            df: 龙虎榜数据
            
        Returns:
            格式化字符串
        """
        if df is None or df.empty:
            return "无数据"
        
        df = df.head(10)
        
        lines = ["代码\t名称\t收盘价\t涨跌幅\t买入营业部\t卖出营业部"]
        
        for _, row in df.iterrows():
            code = row.get('ts_code', '')
            name = row.get('name', '')
            close = row.get('close', 0) or 0
            pct = row.get('pct_chg', 0) or 0
            buy = row.get('buy', '')
            sell = row.get('sell', '')
            
            lines.append(f"{code}\t{name}\t{close:.2f}\t{pct:.2f}%\t{buy}\t{sell}")
        
        return "\n".join(lines)


_market_service: Optional[MarketService] = None


def get_market_service() -> MarketService:
    """获取特色数据服务单例"""
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
    return _market_service
