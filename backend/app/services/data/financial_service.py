"""
财务数据服务
提供财务报表、指标、股东等信息
"""
import logging
from typing import Optional, Dict, Any
import pandas as pd

from .tushare_client import get_tushare_client
from .stock_service import get_stock_service
from app.services.logging_manager import get_logger

logger = get_logger("data.financial_service")


class FinancialService:
    """财务数据服务类"""
    
    def __init__(self):
        self.tushare = get_tushare_client()
        self.stock = get_stock_service()
    
    def get_fina_indicator(self, stock_code: str, limit: int = 4) -> Optional[pd.DataFrame]:
        """
        获取财务指标
        
        Args:
            stock_code: 股票代码
            limit: 返回数量
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        return self.tushare.get_fina_indicator(ts_code, limit)
    
    def get_income(self, stock_code: str, limit: int = 4) -> Optional[pd.DataFrame]:
        """
        获取利润表
        
        Args:
            stock_code: 股票代码
            limit: 返回数量
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        return self.tushare.get_income(ts_code, limit)
    
    def get_balance_sheet(self, stock_code: str, limit: int = 4) -> Optional[pd.DataFrame]:
        """
        获取资产负债表
        
        Args:
            stock_code: 股票代码
            limit: 返回数量
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        return self.tushare.get_balance_sheet(ts_code, limit)
    
    def get_cashflow(self, stock_code: str, limit: int = 4) -> Optional[pd.DataFrame]:
        """
        获取现金流量表
        
        Args:
            stock_code: 股票代码
            limit: 返回数量
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        return self.tushare.get_cashflow(ts_code, limit)
    
    def get_top10_holders(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取前十大股东
        
        Args:
            stock_code: 股票代码
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        return self.tushare.get_top10_holders(ts_code)
    
    def get_holdernum(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取股东人数
        
        Args:
            stock_code: 股票代码
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        return self.tushare.get_stk_holdernum(ts_code)
    
    def get_dividend(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取分红送配信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        return self.tushare.get_dividend(ts_code)
    
    def get_fina_mainbz(self, stock_code: str, limit: int = 4) -> Optional[pd.DataFrame]:
        """
        获取主营业务构成
        
        Args:
            stock_code: 股票代码
            limit: 返回数量
            
        Returns:
            DataFrame
        """
        if not self.tushare.is_connected:
            return None
        
        ts_code = self.stock.normalize_code(stock_code)
        return self.tushare.get_fina_mainbz(ts_code, limit)
    
    def get_all_financials(self, stock_code: str, limit: int = 4) -> Dict[str, Any]:
        """
        获取完整财务数据
        
        Args:
            stock_code: 股票代码
            limit: 返回数量
            
        Returns:
            包含多种财务数据的字典
        """
        ts_code = self.stock.normalize_code(stock_code)
        
        result = {
            "stock_code": stock_code,
            "ts_code": ts_code,
            "fina_indicator": None,
            "income": None,
            "balance_sheet": None,
            "cashflow": None,
            "top10_holders": None,
            "dividend": None,
        }
        
        if not self.tushare.is_connected:
            return result
        
        try:
            result["fina_indicator"] = self.tushare.get_fina_indicator(ts_code, limit)
            result["income"] = self.tushare.get_income(ts_code, limit)
            result["balance_sheet"] = self.tushare.get_balance_sheet(ts_code, limit)
            result["cashflow"] = self.tushare.get_cashflow(ts_code, limit)
            result["top10_holders"] = self.tushare.get_top10_holders(ts_code)
            result["dividend"] = self.tushare.get_dividend(ts_code)
        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
        
        return result
    
    def format_fina_indicator(self, df: pd.DataFrame) -> str:
        """
        格式化财务指标
        
        Args:
            df: 财务指标数据
            
        Returns:
            格式化字符串
        """
        if df is None or df.empty:
            return "无数据"
        
        df = df.head(1)
        row = df.iloc[0]
        
        period = row.get('end_date', 'N/A')
        if isinstance(period, str) and len(period) == 8:
            period = f"{period[:4]}-{period[4:6]}-{period[6:]}"
        
        return f"""
报告期: {period}
净资产收益率(ROE): {row.get('roe', 'N/A')}%
资产负债率: {row.get('debt_to_assets', 'N/A')}%
毛利率: {row.get('grossprofit_margin', 'N/A')}%
净利率: {row.get('netprofit_margin', 'N/A')}%
每股收益(EPS): {row.get('eps', 'N/A')}
每股净资产(BPS): {row.get('bps', 'N/A')}
营业收入增长率: {row.get('revenue_growth_yoy', 'N/A')}%
净利润增长率: {row.get('netprofit_growth_yoy', 'N/A')}%
"""


_financial_service: Optional[FinancialService] = None


def get_financial_service() -> FinancialService:
    """获取财务服务单例"""
    global _financial_service
    if _financial_service is None:
        _financial_service = FinancialService()
    return _financial_service
