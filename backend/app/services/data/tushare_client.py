"""
Tushare 客户端封装
提供 A 股市场的数据获取功能
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd
from app.services.logging_manager import get_logger

logger = get_logger("data.tushare_client")

TUSHARE_AVAILABLE = True
try:
    import tushare as ts
except ImportError:
    TUSHARE_AVAILABLE = False
    logger.warning("Tushare 未安装，请运行: pip install tushare")


class TushareClient:
    """Tushare 客户端封装类"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化 Tushare 客户端
        
        Args:
            token: Tushare Token，默认从环境变量 TUSHARE_TOKEN 读取
        """
        self.token = token or os.getenv('TUSHARE_TOKEN')
        self.api = None
        self._connected = False
        
        if self.token:
            self.connect()
    
    def connect(self) -> bool:
        """连接到 Tushare"""
        if not TUSHARE_AVAILABLE:
            logger.error("Tushare 库不可用")
            return False
        
        if not self.token:
            logger.warning("未配置 Tushare Token")
            return False
        
        try:
            self.api = ts.pro_api(self.token)
            self._connected = True
            logger.info("Tushare 连接成功")
            return True
        except Exception as e:
            logger.error(f"Tushare 连接失败: {e}")
            self._connected = False
            return False
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self.api is not None
    
    def _normalize_ts_code(self, stock_code: str) -> str:
        """
        标准化股票代码为 Tushare 格式
        
        Args:
            stock_code: 股票代码，如 000001, 600000
            
        Returns:
            标准化后的股票代码，如 000001.SZ, 600000.SH
        """
        stock_code = stock_code.strip().upper()
        
        # 移除可能的后缀
        for suffix in ['.SH', '.SZ', '.XSHG', '.XSGE']:
            stock_code = stock_code.replace(suffix, '')
        
        # 根据代码规则添加市场后缀
        if stock_code.startswith('6') or stock_code.startswith('9'):
            return f"{stock_code}.SH"  # 上海证券交易所
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            return f"{stock_code}.SZ"  # 深圳证券交易所
        elif stock_code.startswith('8') or stock_code.startswith('4'):
            return f"{stock_code}.BJ"  # 北京证券交易所
        else:
            return f"{stock_code}.SZ"  # 默认深圳
    
    def get_stock_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取股票日线数据
        
        Args:
            ts_code: 股票代码 (如 000001.SZ)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            logger.error(f"获取日线数据失败: {e}")
            return None
    
    def get_stock_minute(self, ts_code: str, start_time: str, end_time: str, freq: str = "5") -> Optional[pd.DataFrame]:
        """
        获取股票分钟线数据
        
        Args:
            ts_code: 股票代码 (如 000001.SZ)
            start_time: 开始时间 (YYYYMMDD HH:MM:SS)
            end_time: 结束时间 (YYYYMMDD HH:MM:SS)
            freq: 频率 (1/5/15/30/60 分钟)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.minute(ts_code=ts_code, start_time=start_time, end_time=end_time, freq=freq)
            return df
        except Exception as e:
            logger.error(f"获取分钟线数据失败: {e}")
            return None
    
    def get_realtime_quote(self, ts_code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情
        
        Args:
            ts_code: 股票代码 (如 000001.SZ)
            
        Returns:
            行情字典或 None
        """
        if not TUSHARE_AVAILABLE:
            return None
        
        try:
            df = ts.realtime_quote(ts_code=ts_code)
            if df is not None and not df.empty:
                return df.iloc[0].to_dict()
            return None
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return None
    
    def get_realtime_quotes_batch(self, ts_codes: List[str]) -> Optional[pd.DataFrame]:
        """
        批量获取实时行情
        
        Args:
            ts_codes: 股票代码列表
            
        Returns:
            DataFrame 或 None
        """
        if not TUSHARE_AVAILABLE:
            return None
        
        try:
            df = ts.realtime_quote(ts_code=','.join(ts_codes))
            return df
        except Exception as e:
            logger.error(f"批量获取实时行情失败: {e}")
            return None
    
    def get_fina_indicator(self, ts_code: str, limit: int = 4) -> Optional[pd.DataFrame]:
        """
        获取财务指标
        
        Args:
            ts_code: 股票代码
            limit: 返回记录数，默认获取最近4个季度
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.fina_indicator(ts_code=ts_code, limit=limit)
            return df
        except Exception as e:
            logger.error(f"获取财务指标失败: {e}")
            return None
    
    def get_income(self, ts_code: str, limit: int = 4) -> Optional[pd.DataFrame]:
        """
        获取利润表数据
        
        Args:
            ts_code: 股票代码
            limit: 返回记录数
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.income(ts_code=ts_code, limit=limit)
            return df
        except Exception as e:
            logger.error(f"获取利润表失败: {e}")
            return None
    
    def get_balance_sheet(self, ts_code: str, limit: int = 4) -> Optional[pd.DataFrame]:
        """
        获取资产负债表
        
        Args:
            ts_code: 股票代码
            limit: 返回记录数
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.balancesheet(ts_code=ts_code, limit=limit)
            return df
        except Exception as e:
            logger.error(f"获取资产负债表失败: {e}")
            return None
    
    def get_cashflow(self, ts_code: str, limit: int = 4) -> Optional[pd.DataFrame]:
        """
        获取现金流量表
        
        Args:
            ts_code: 股票代码
            limit: 返回记录数
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.cashflow(ts_code=ts_code, limit=limit)
            return df
        except Exception as e:
            logger.error(f"获取现金流量表失败: {e}")
            return None
    
    def get_margin(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取融资融券数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.margin(ts_code=ts_code, start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            logger.error(f"获取融资融券数据失败: {e}")
            return None
    
    def get_margin_detail(self, ts_code: str, trade_date: str) -> Optional[pd.DataFrame]:
        """
        获取融资融券明细
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.margin_detail(ts_code=ts_code, trade_date=trade_date)
            return df
        except Exception as e:
            logger.error(f"获取融资融券明细失败: {e}")
            return None
    
    def get_moneyflow(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取资金流向数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            logger.error(f"获取资金流向失败: {e}")
            return None
    
    def get_top_inst(self, trade_date: str) -> Optional[pd.DataFrame]:
        """
        获取龙虎榜机构明细
        
        Args:
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.top_inst(trade_date=trade_date)
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜失败: {e}")
            return None
    
    def get_top_list(self, trade_date: str) -> Optional[pd.DataFrame]:
        """
        获取龙虎榜上榜股票
        
        Args:
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.top_list(trade_date=trade_date)
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜上榜股票失败: {e}")
            return None
    
    def get_stk_holdertrade(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取限售股解禁
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.stk_holdertrade(ts_code=ts_code, start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            logger.error(f"获取限售股解禁失败: {e}")
            return None
    
    def get_dividend(self, ts_code: str) -> Optional[pd.DataFrame]:
        """
        获取分红送配信息
        
        Args:
            ts_code: 股票代码
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.dividend(ts_code=ts_code)
            return df
        except Exception as e:
            logger.error(f"获取分红送配失败: {e}")
            return None
    
    def get_fina_mainbz(self, ts_code: str, limit: int = 4) -> Optional[pd.DataFrame]:
        """
        获取主营业务构成
        
        Args:
            ts_code: 股票代码
            limit: 返回记录数
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.fina_mainbz(ts_code=ts_code, limit=limit)
            return df
        except Exception as e:
            logger.error(f"获取主营业务构成失败: {e}")
            return None
    
    def get_stk_holdernum(self, ts_code: str) -> Optional[pd.DataFrame]:
        """
        获取股东人数
        
        Args:
            ts_code: 股票代码
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.stk_holdernum(ts_code=ts_code)
            return df
        except Exception as e:
            logger.error(f"获取股东人数失败: {e}")
            return None
    
    def get_top10_holders(self, ts_code: str) -> Optional[pd.DataFrame]:
        """
        获取前十大股东
        
        Args:
            ts_code: 股票代码
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.top10_holders(ts_code=ts_code)
            return df
        except Exception as e:
            logger.error(f"获取前十大股东失败: {e}")
            return None
    
    def get_stock_basic(self, exchange: str = "") -> Optional[pd.DataFrame]:
        """
        获取股票基本信息
        
        Args:
            exchange: 交易所 (SSE/SZSE/BSE)，空为全部
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.stock_basic(exchange=exchange)
            return df
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            return None
    
    def get_daily_basic(self, trade_date: str) -> Optional[pd.DataFrame]:
        """
        获取每日交易统计
        
        Args:
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.daily_basic(trade_date=trade_date)
            return df
        except Exception as e:
            logger.error(f"获取每日交易统计失败: {e}")
            return None
    
    def get_zz_index_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取中证指数日线
        
        Args:
            ts_code: 指数代码 (如 000300.SH)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.zz_index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            logger.error(f"获取中证指数日线失败: {e}")
            return None
    
    def get_fund_basic(self, market: str = "E") -> Optional[pd.DataFrame]:
        """
        获取基金基本信息
        
        Args:
            market: 市场类型 (E=场内基金, O=场外基金)
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.fund_basic(market=market)
            return df
        except Exception as e:
            logger.error(f"获取基金基本信息失败: {e}")
            return None
    
    def get_fund_nav(self, ts_code: str) -> Optional[pd.DataFrame]:
        """
        获取基金净值
        
        Args:
            ts_code: 基金代码
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_connected:
            logger.warning("Tushare 未连接")
            return None
        
        try:
            df = self.api.fund_nav(ts_code=ts_code)
            return df
        except Exception as e:
            logger.error(f"获取基金净值失败: {e}")
            return None


_tushare_client: Optional[TushareClient] = None


def get_tushare_client() -> TushareClient:
    """获取 Tushare 客户端单例"""
    global _tushare_client
    if _tushare_client is None:
        _tushare_client = TushareClient()
    return _tushare_client
