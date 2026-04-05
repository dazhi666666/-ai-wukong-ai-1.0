"""
AKShare 客户端封装
提供 A 股、指数、基金等市场数据获取功能
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd
from app.services.logging_manager import get_logger

logger = get_logger("data.akshare_client")

AKSHARE_AVAILABLE = True
try:
    import akshare as ak
except ImportError:
    AKSHARE_AVAILABLE = False
    logger.warning("AKShare 未安装，请运行: pip install akshare")


class AKShareClient:
    """AKShare 客户端封装类"""
    
    def __init__(self):
        """初始化 AKShare 客户端"""
        if not AKSHARE_AVAILABLE:
            logger.warning("AKShare 库不可用")
    
    @property
    def is_available(self) -> bool:
        """检查是否可用"""
        return AKSHARE_AVAILABLE
    
    def get_stock_daily(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取 A 股日线数据
        
        Args:
            symbol: 股票代码 (如 000001)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            return df
        except Exception as e:
            logger.error(f"获取A股日线失败: {e}")
            return None
    
    def get_stock_daily_hfq(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取 A 股日线数据（后复权）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="hfq"
            )
            return df
        except Exception as e:
            logger.error(f"获取A股日线(后复权)失败: {e}")
            return None
    
    def get_stock_realtime(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取 A 股实时行情
        
        Args:
            symbol: 股票代码
            
        Returns:
            行情字典或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zh_a_spot_em()
            result = df[df['代码'] == symbol]
            if not result.empty:
                return result.iloc[0].to_dict()
            return None
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return None
    
    def get_stock_realtime_batch(self, symbols: List[str]) -> Optional[pd.DataFrame]:
        """
        批量获取 A 股实时行情
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zh_a_spot_em()
            result = df[df['代码'].isin(symbols)]
            return result
        except Exception as e:
            logger.error(f"批量获取实时行情失败: {e}")
            return None
    
    def get_index_daily(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取指数日线数据
        
        Args:
            symbol: 指数代码 (如 000001, 399001)
                - 000001: 上证指数
                - 399001: 深证成指
                - 399006: 创业板指
                - 000300: 沪深300
                
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zh_index_daily(symbol=f"sh{symbol}")
            return df
        except Exception as e:
            logger.error(f"获取指数日线失败: {e}")
            return None
    
    def get_index_realtime(self) -> Optional[pd.DataFrame]:
        """
        获取主要指数实时行情
        
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zh_index_spot_em()
            return df
        except Exception as e:
            logger.error(f"获取指数实时行情失败: {e}")
            return None
    
    def get_fund_etf_spot(self) -> Optional[pd.DataFrame]:
        """
        获取 ETF 实时行情
        
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.fund_etf_spot_em()
            return df
        except Exception as e:
            logger.error(f"获取ETF行情失败: {e}")
            return None
    
    def get_fund_lof_spot(self) -> Optional[pd.DataFrame]:
        """
        获取 LOF 实时行情
        
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.fund_lof_spot_em()
            return df
        except Exception as e:
            logger.error(f"获取LOF行情失败: {e}")
            return None
    
    def get_fund_etf_hist(self, symbol: str, period: str = "daily") -> Optional[pd.DataFrame]:
        """
        获取 ETF 历史数据
        
        Args:
            symbol: ETF 代码
            period: 周期 (daily/weekly/monthly)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.fund_etf_hist_em(symbol=symbol, period=period)
            return df
        except Exception as e:
            logger.error(f"获取ETF历史数据失败: {e}")
            return None
    
    def get_moneyflow_hsgt(self) -> Optional[pd.DataFrame]:
        """
        获取北向资金流向
        
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_moneyflow_hsgt()
            return df
        except Exception as e:
            logger.error(f"获取北向资金流向失败: {e}")
            return None
    
    def get_moneyflow_hsgt_summary(self) -> Optional[pd.DataFrame]:
        """
        获取北向资金流向统计
        
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_moneyflow_hsgt_summary()
            return df
        except Exception as e:
            logger.error(f"获取北向资金统计失败: {e}")
            return None
    
    def get_stock_individual_flow(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取个股资金流向
        
        Args:
            symbol: 股票代码
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_individual_fund_flow(stock=symbol)
            return df
        except Exception as e:
            logger.error(f"获取个股资金流向失败: {e}")
            return None
    
    def get_stock_individual_flow_minute(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取个股资金流向（分钟级）
        
        Args:
            symbol: 股票代码
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = stock_individual_fund_flow_minute(stock=symbol)
            return df
        except Exception as e:
            logger.error(f"获取分钟级资金流向失败: {e}")
            return None
    
    def get_stock_market_fund_flow(self) -> Optional[pd.DataFrame]:
        """
        获取市场资金流向
        
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_market_fund_flow()
            return df
        except Exception as e:
            logger.error(f"获取市场资金流向失败: {e}")
            return None
    
    def get_stock_zh_a_newest(self) -> Optional[pd.DataFrame]:
        """
        获取 A 股最新上市股票
        
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zh_a_newest()
            return df
        except Exception as e:
            logger.error(f"获取最新上市股票失败: {e}")
            return None
    
    def get_stock_info_global_sina(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取个股信息（新浪）
        
        Args:
            symbol: 股票代码
            
        Returns:
            字典或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_info_global_sina(symbol=symbol)
            if df is not None and not df.empty:
                return df.to_dict()
            return None
        except Exception as e:
            logger.error(f"获取个股信息失败: {e}")
            return None
    
    def get_stock_news_em(self, symbol: str = "") -> Optional[pd.DataFrame]:
        """
        获取财经新闻
        
        Args:
            symbol: 股票代码（可选）
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            if symbol:
                df = ak.stock_news_em(symbol=symbol)
            else:
                df = ak.stock_news_em()
            return df
        except Exception as e:
            logger.error(f"获取财经新闻失败: {e}")
            return None
    
    def get_stock_hot_keyword(self) -> Optional[pd.DataFrame]:
        """
        获取市场热点关键词
        
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_hot_keyword()
            return df
        except Exception as e:
            logger.error(f"获取热点关键词失败: {e}")
            return None
    
    def get_stock_board_industry_name_em(self) -> Optional[pd.DataFrame]:
        """
        获取板块行业列表
        
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_board_industry_name_em()
            return df
        except Exception as e:
            logger.error(f"获取板块行业列表失败: {e}")
            return None
    
    def get_stock_board_industry_cons_em(self, name: str) -> Optional[pd.DataFrame]:
        """
        获取板块成分股
        
        Args:
            name: 板块名称
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_board_industry_cons_em(symbol=name)
            return df
        except Exception as e:
            logger.error(f"获取板块成分股失败: {e}")
            return None
    
    def get_stock_fund_flow_industry(self, n: int = 5) -> Optional[pd.DataFrame]:
        """
        获取行业资金流向
        
        Args:
            n: 返回数量
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_fund_flow_industry(n=n)
            return df
        except Exception as e:
            logger.error(f"获取行业资金流向失败: {e}")
            return None
    
    def get_stock_fund_flow_concept(self, n: int = 5) -> Optional[pd.DataFrame]:
        """
        获取概念资金流向
        
        Args:
            n: 返回数量
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_fund_flow_concept(n=n)
            return df
        except Exception as e:
            logger.error(f"获取概念资金流向失败: {e}")
            return None
    
    def get_stock_zt_pool(self, date: str) -> Optional[pd.DataFrame]:
        """
        获取涨停板池
        
        Args:
            date: 日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zt_pool(date=date)
            return df
        except Exception as e:
            logger.error(f"获取涨停板池失败: {e}")
            return None
    
    def get_stock_zt_pool_subnew(self, date: str) -> Optional[pd.DataFrame]:
        """
        获取次新股涨停池
        
        Args:
            date: 日期
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zt_pool_subnew(date=date)
            return df
        except Exception as e:
            logger.error(f"获取次新股涨停池失败: {e}")
            return None
    
    def get_stock_zt_pool_strong(self, date: str) -> Optional[pd.DataFrame]:
        """
        获取强势股池
        
        Args:
            date: 日期
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zt_pool_strong(date=date)
            return df
        except Exception as e:
            logger.error(f"获取强势股池失败: {e}")
            return None
    
    def get_stock_kline(self, symbol: str, adjust: str = "qfq") -> Optional[pd.DataFrame]:
        """
        获取股票K线数据
        
        Args:
            symbol: 股票代码
            adjust: 复权类型 (qfq/hfq)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.stock_zh_a_kline(symbol=symbol, adjust=adjust)
            return df
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return None
    
    def get_index_weight(self, index_code: str) -> Optional[pd.DataFrame]:
        """
        获取指数成分股权重
        
        Args:
            index_code: 指数代码 (如 000300.SH)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.index_stock_cons(index_code=index_code)
            return df
        except Exception as e:
            logger.error(f"获取指数成分股权重失败: {e}")
            return None
    
    def get_fund_portfolio(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取基金持仓
        
        Args:
            symbol: 基金代码
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.fund_portfolio(symbol=symbol)
            return df
        except Exception as e:
            logger.error(f"获取基金持仓失败: {e}")
            return None
    
    def get_fund_spot(self) -> Optional[pd.DataFrame]:
        """
        获取场外基金实时行情
        
        Returns:
            DataFrame 或 None
        """
        if not self.is_available:
            return None
        
        try:
            df = ak.fund_otc_spot()
            return df
        except Exception as e:
            logger.error(f"获取场外基金行情失败: {e}")
            return None


_akshare_client: Optional[AKShareClient] = None


def get_akshare_client() -> AKShareClient:
    """获取 AKShare 客户端单例"""
    global _akshare_client
    if _akshare_client is None:
        _akshare_client = AKShareClient()
    return _akshare_client
