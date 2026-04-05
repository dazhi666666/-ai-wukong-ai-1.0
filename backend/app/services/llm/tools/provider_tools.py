"""
LangChain Tools - 按数据源分类的股票数据工具
不同数据源作为不同的 Tools 供大模型调用
"""
import asyncio
import logging
from typing import Annotated
from datetime import datetime, timedelta

from langchain_core.tools import tool

from app.services.stock_data.factory import get_stock_provider
from app.services.stock_data.providers.juhe import format_stock_data_for_prompt
from app.services.logging_manager import get_logger

logger = get_logger("provider_tools")

# 数据源信息
PROVIDER_INFO = {
    "juhe": {"name": "Juhe聚合数据", "category": "数据源"},
    "tushare": {"name": "Tushare", "category": "数据源"},
    "akshare": {"name": "AKShare", "category": "数据源"},
    "baostock": {"name": "BaoStock", "category": "数据源"},
}


def get_provider_name(provider: str) -> str:
    """获取数据源中文名称"""
    return PROVIDER_INFO.get(provider, {}).get("name", provider)


async def _get_quote_async(provider_name: str, stock_code: str):
    """异步获取实时行情"""
    provider = get_stock_provider(provider_name)
    if not provider:
        return None
    if not provider.connected:
        await provider.connect()
    return await provider.get_quotes(stock_code)


async def _get_daily_async(provider_name: str, stock_code: str, days: int):
    """异步获取历史日线"""
    provider = get_stock_provider(provider_name)
    if not provider or not provider.connected:
        return None
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return await provider.get_historical(stock_code, start_date, end_date, "daily")


async def _get_financial_async(provider_name: str, stock_code: str):
    """异步获取财务数据"""
    provider = get_stock_provider(provider_name)
    if not provider or not provider.connected:
        return None
    return await provider.get_financial(stock_code)


async def _get_moneyflow_async(provider_name: str, stock_code: str, days: int):
    """异步获取资金流向"""
    provider = get_stock_provider(provider_name)
    if not provider or not provider.connected:
        return None
    return await provider.get_moneyflow(stock_code, days)


async def _get_margin_async(provider_name: str, stock_code: str, days: int):
    """异步获取融资融券"""
    provider = get_stock_provider(provider_name)
    if not provider or not provider.connected:
        return None
    return await provider.get_margin(stock_code, days)


async def _get_stock_info_async(provider_name: str, stock_code: str):
    """异步获取股票基本信息"""
    provider = get_stock_provider(provider_name)
    if not provider or not provider.connected:
        return None
    if not hasattr(provider, 'get_stock_basic_info'):
        return None
    return await provider.get_stock_basic_info(stock_code)


# ==================== Juhe 聚合数据 Tools ====================

@tool
def get_stock_quote_juhe(stock_code: Annotated[str, "股票代码，如 000001、600000"]) -> str:
    """
    【Juhe聚合数据】获取股票实时行情
    
    数据源: 聚合数据 (Juhe)
    适用: A股实时行情、五档盘口
    
    Args:
        stock_code: 股票代码
        
    Returns:
        格式化后的实时行情数据
    """
    try:
        quote = asyncio.run(_get_quote_async("juhe", stock_code))
        
        if not quote:
            return f"未能通过 Juhe 获取股票 {stock_code} 的行情数据"
        
        return format_stock_data_for_prompt(quote, include_order_book=True)
    except Exception as e:
        logger.error(f"Juhe 获取行情失败: {e}")
        return f"获取行情失败: {str(e)}"


@tool
def get_stock_daily_juhe(
    stock_code: Annotated[str, "股票代码"],
    days: Annotated[int, "获取天数，默认30天"] = 30
) -> str:
    """
    【Juhe聚合数据】获取股票历史日线
    
    数据源: 聚合数据 (Juhe)
    
    Args:
        stock_code: 股票代码
        days: 获取天数
        
    Returns:
        历史日线数据
    """
    try:
        data = asyncio.run(_get_daily_async("juhe", stock_code, days))
        
        if data is None:
            return f"未能通过 Juhe 获取股票 {stock_code} 的历史数据"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("daily", data, limit=days)
    except Exception as e:
        logger.error(f"Juhe 获取日线失败: {e}")
        return f"获取日线失败: {str(e)}"


# ==================== Tushare Tools ====================

@tool
def get_stock_quote_tushare(stock_code: Annotated[str, "股票代码，如 000001、600000"]) -> str:
    """
    【Tushare】获取股票实时行情
    
    数据源: Tushare
    适用: A股实时行情
    
    Args:
        stock_code: 股票代码
        
    Returns:
        格式化后的实时行情数据
    """
    try:
        quote = asyncio.run(_get_quote_async("tushare", stock_code))
        
        if not quote:
            return f"未能通过 Tushare 获取股票 {stock_code} 的行情数据"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("quote", quote)
    except Exception as e:
        logger.error(f"Tushare 获取行情失败: {e}")
        return f"获取行情失败: {str(e)}"


@tool
def get_stock_daily_tushare(
    stock_code: Annotated[str, "股票代码"],
    days: Annotated[int, "获取天数，默认30天"] = 30
) -> str:
    """
    【Tushare】获取股票历史日线
    
    数据源: Tushare
    
    Args:
        stock_code: 股票代码
        days: 获取天数
        
    Returns:
        历史日线数据
    """
    try:
        data = asyncio.run(_get_daily_async("tushare", stock_code, days))
        
        if data is None:
            return f"未能通过 Tushare 获取股票 {stock_code} 的历史数据"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("daily", data, limit=days)
    except Exception as e:
        logger.error(f"Tushare 获取日线失败: {e}")
        return f"获取日线失败: {str(e)}"


@tool
def get_fina_indicator_tushare(
    stock_code: Annotated[str, "股票代码"],
    periods: Annotated[int, "获取报告期数量，默认4个"] = 4
) -> str:
    """
    【Tushare】获取股票财务指标
    
    数据源: Tushare
    适用: ROE、毛利率、净利率等
    
    Args:
        stock_code: 股票代码
        periods: 获取报告期数量
        
    Returns:
        财务指标数据
    """
    try:
        data = asyncio.run(_get_financial_async("tushare", stock_code))
        
        if not data:
            return f"未能通过 Tushare 获取股票 {stock_code} 的财务数据"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("financial", data)
    except Exception as e:
        logger.error(f"Tushare 获取财务数据失败: {e}")
        return f"获取财务数据失败: {str(e)}"


@tool
def get_moneyflow_tushare(
    stock_code: Annotated[str, "股票代码"],
    days: Annotated[int, "获取天数，默认10天"] = 10
) -> str:
    """
    【Tushare】获取股票资金流向
    
    数据源: Tushare
    适用: 主力资金、超大单等
    
    Args:
        stock_code: 股票代码
        days: 获取天数
        
    Returns:
        资金流向数据
    """
    try:
        data = asyncio.run(_get_moneyflow_async("tushare", stock_code, days))
        
        if not data:
            return f"未能通过 Tushare 获取股票 {stock_code} 的资金流向"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("moneyflow", data)
    except Exception as e:
        logger.error(f"Tushare 获取资金流向失败: {e}")
        return f"获取资金流向失败: {str(e)}"


@tool
def get_margin_tushare(
    stock_code: Annotated[str, "股票代码"],
    days: Annotated[int, "获取天数，默认10天"] = 10
) -> str:
    """
    【Tushare】获取融资融券数据
    
    数据源: Tushare
    适用: 融资余额、融券余额等
    
    Args:
        stock_code: 股票代码
        days: 获取天数
        
    Returns:
        融资融券数据
    """
    try:
        data = asyncio.run(_get_margin_async("tushare", stock_code, days))
        
        if not data:
            return f"未能通过 Tushare 获取股票 {stock_code} 的融资融券数据"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("margin", data)
    except Exception as e:
        logger.error(f"Tushare 获取融资融券失败: {e}")
        return f"获取融资融券失败: {str(e)}"


# ==================== AKShare Tools ====================

@tool
def get_stock_quote_akshare(stock_code: Annotated[str, "股票代码，如 000001、600000"]) -> str:
    """
    【AKShare】获取股票实时行情
    
    数据源: AKShare
    适用: A股、港股、美股实时行情
    
    Args:
        stock_code: 股票代码
        
    Returns:
        格式化后的实时行情数据
    """
    try:
        quote = asyncio.run(_get_quote_async("akshare", stock_code))
        
        if not quote:
            return f"未能通过 AKShare 获取股票 {stock_code} 的行情数据"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("quote", quote)
    except Exception as e:
        logger.error(f"AKShare 获取行情失败: {e}")
        return f"获取行情失败: {str(e)}"


@tool
def get_stock_daily_akshare(
    stock_code: Annotated[str, "股票代码"],
    days: Annotated[int, "获取天数，默认30天"] = 30
) -> str:
    """
    【AKShare】获取股票历史日线
    
    数据源: AKShare
    
    Args:
        stock_code: 股票代码
        days: 获取天数
        
    Returns:
        历史日线数据
    """
    try:
        data = asyncio.run(_get_daily_async("akshare", stock_code, days))
        
        if data is None:
            return f"未能通过 AKShare 获取股票 {stock_code} 的历史数据"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("daily", data, limit=days)
    except Exception as e:
        logger.error(f"AKShare 获取日线失败: {e}")
        return f"获取日线失败: {str(e)}"


@tool
def get_fina_indicator_akshare(
    stock_code: Annotated[str, "股票代码"],
    periods: Annotated[int, "获取报告期数量，默认4个"] = 4
) -> str:
    """
    【AKShare】获取股票财务指标
    
    数据源: AKShare
    适用: ROE、毛利率、净利率等
    
    Args:
        stock_code: 股票代码
        periods: 获取报告期数量
        
    Returns:
        财务指标数据
    """
    try:
        data = asyncio.run(_get_financial_async("akshare", stock_code))
        
        if not data:
            return f"未能通过 AKShare 获取股票 {stock_code} 的财务数据"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("financial", data)
    except Exception as e:
        logger.error(f"AKShare 获取财务数据失败: {e}")
        return f"获取财务数据失败: {str(e)}"


# ==================== BaoStock Tools ====================

@tool
def get_stock_quote_baostock(stock_code: Annotated[str, "股票代码，如 000001、600000"]) -> str:
    """
    【BaoStock】获取股票实时行情
    
    数据源: BaoStock
    适用: A股实时行情
    
    Args:
        stock_code: 股票代码
        
    Returns:
        格式化后的实时行情数据
    """
    try:
        quote = asyncio.run(_get_quote_async("baostock", stock_code))
        
        if not quote:
            return f"未能通过 BaoStock 获取股票 {stock_code} 的行情数据"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("quote", quote)
    except Exception as e:
        logger.error(f"BaoStock 获取行情失败: {e}")
        return f"获取行情失败: {str(e)}"


@tool
def get_stock_daily_baostock(
    stock_code: Annotated[str, "股票代码"],
    days: Annotated[int, "获取天数，默认30天"] = 30
) -> str:
    """
    【BaoStock】获取股票历史日线
    
    数据源: BaoStock
    
    Args:
        stock_code: 股票代码
        days: 获取天数
        
    Returns:
        历史日线数据
    """
    try:
        data = asyncio.run(_get_daily_async("baostock", stock_code, days))
        
        if data is None:
            return f"未能通过 BaoStock 获取股票 {stock_code} 的历史数据"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("daily", data, limit=days)
    except Exception as e:
        logger.error(f"BaoStock 获取日线失败: {e}")
        return f"获取日线失败: {str(e)}"


@tool
def get_stock_info_baostock(stock_code: Annotated[str, "股票代码"]) -> str:
    """
    【BaoStock】获取股票基本信息
    
    数据源: BaoStock
    适用: 股票基本信息、行业、市值等
    
    Args:
        stock_code: 股票代码
        
    Returns:
        股票基本信息
    """
    try:
        data = asyncio.run(_get_stock_info_async("baostock", stock_code))
        
        if not data:
            return f"未能通过 BaoStock 获取股票 {stock_code} 的基本信息"
        
        from app.services.stock_data import format_stock_data
        return format_stock_data("quote", data)
    except Exception as e:
        logger.error(f"BaoStock 获取基本信息失败: {e}")
        return f"获取基本信息失败: {str(e)}"


# ==================== BaoStock 扩展工具 ====================
from app.services.llm.tools.baostock_tools import (
    get_stock_daily_baostock,
    get_stock_weekly_baostock,
    get_stock_monthly_baostock,
    get_stock_valuation_baostock,
    get_stock_profit_baostock,
    get_stock_balance_baostock,
    get_stock_cashflow_baostock,
    get_hs300_constituents_baostock,
    get_sz50_constituents_baostock,
    get_zz500_constituents_baostock,
    get_stock_industry_baostock,
    get_trade_calendar_baostock,
    get_stock_info_baostock,
)

# ==================== AkShare 扩展工具 ====================
from app.services.llm.tools.akshare_tools import (
    get_stock_daily_akshare,
    get_stock_realtime_akshare,
    get_stock_minute_akshare,
    get_zt_pool_akshare,
    get_stock_balance_sheet_akshare,
    get_stock_profit_sheet_akshare,
    get_stock_cash_flow_akshare,
    get_stock_financial_indicator_akshare,
    get_stock_valuation_akshare,
    get_stock_fund_flow_akshare,
    get_sector_fund_flow_akshare,
    get_stock_chips_akshare,
    get_holders_akshare,
    get_hsgt_hold_akshare,
    get_hsgt_net_flow_akshare,
    get_industry_list_akshare,
    get_industry_stocks_akshare,
    get_lhb_pool_akshare,
    get_lhb_detail_akshare,
    get_new_stocks_akshare,
    get_margin_akshare,
    get_margin_stock_akshare,
    get_block_trade_akshare,
    get_unlock_akshare,
    get_stock_repurchase_akshare,
    get_stock_incentive_akshare,
    get_earnings_forecast_akshare,
)


# ==================== 导出所有 Tools ====================

PROVIDER_TOOLS = [
    # Juhe
    get_stock_quote_juhe,
    get_stock_daily_juhe,
    # Tushare
    get_stock_quote_tushare,
    get_stock_daily_tushare,
    get_fina_indicator_tushare,
    get_moneyflow_tushare,
    get_margin_tushare,
    # AKShare - 原有
    get_stock_quote_akshare,
    get_stock_daily_akshare,
    get_fina_indicator_akshare,
    # AKShare - 新增 (覆盖原有)
    get_stock_realtime_akshare,
    get_stock_minute_akshare,
    get_zt_pool_akshare,
    get_stock_balance_sheet_akshare,
    get_stock_profit_sheet_akshare,
    get_stock_cash_flow_akshare,
    get_stock_financial_indicator_akshare,
    get_stock_valuation_akshare,
    get_stock_fund_flow_akshare,
    get_sector_fund_flow_akshare,
    get_stock_chips_akshare,
    get_holders_akshare,
    get_hsgt_hold_akshare,
    get_hsgt_net_flow_akshare,
    get_industry_list_akshare,
    get_industry_stocks_akshare,
    get_lhb_pool_akshare,
    get_lhb_detail_akshare,
    get_new_stocks_akshare,
    get_margin_akshare,
    get_margin_stock_akshare,
    get_block_trade_akshare,
    get_unlock_akshare,
    get_stock_repurchase_akshare,
    get_stock_incentive_akshare,
    get_earnings_forecast_akshare,
    # BaoStock - 使用新的 baostock_tools
    get_stock_daily_baostock,
    get_stock_weekly_baostock,
    get_stock_monthly_baostock,
    get_stock_valuation_baostock,
    get_stock_profit_baostock,
    get_stock_balance_baostock,
    get_stock_cashflow_baostock,
    get_hs300_constituents_baostock,
    get_sz50_constituents_baostock,
    get_zz500_constituents_baostock,
    get_stock_industry_baostock,
    get_trade_calendar_baostock,
    get_stock_info_baostock,
]


# 按数据源分组的 Tools
PROVIDER_TOOLS_GROUPED = {
    "juhe": {
        "name": "Juhe 聚合数据",
        "description": "聚合数据 API，提供实时行情和历史数据",
        "tools": [get_stock_quote_juhe, get_stock_daily_juhe],
    },
    "tushare": {
        "name": "Tushare",
        "description": "Tushare Pro API，提供行情、财务、资金等全面数据",
        "tools": [
            get_stock_quote_tushare,
            get_stock_daily_tushare,
            get_fina_indicator_tushare,
            get_moneyflow_tushare,
            get_margin_tushare,
        ],
    },
    "akshare": {
        "name": "AKShare",
        "description": "AKShare 开源金融数据 API，支持 A股全量数据",
        "tools": [
            get_stock_daily_akshare,
            get_stock_realtime_akshare,
            get_stock_minute_akshare,
            get_zt_pool_akshare,
            get_stock_balance_sheet_akshare,
            get_stock_profit_sheet_akshare,
            get_stock_cash_flow_akshare,
            get_stock_financial_indicator_akshare,
            get_stock_valuation_akshare,
            get_stock_fund_flow_akshare,
            get_sector_fund_flow_akshare,
            get_stock_chips_akshare,
            get_holders_akshare,
            get_hsgt_hold_akshare,
            get_hsgt_net_flow_akshare,
            get_industry_list_akshare,
            get_industry_stocks_akshare,
            get_lhb_pool_akshare,
            get_lhb_detail_akshare,
            get_new_stocks_akshare,
            get_margin_akshare,
            get_margin_stock_akshare,
            get_block_trade_akshare,
            get_unlock_akshare,
            get_stock_repurchase_akshare,
            get_stock_incentive_akshare,
            get_earnings_forecast_akshare,
        ],
    },
    "baostock": {
        "name": "BaoStock",
        "description": "BaoStock 股票数据 API，提供历史行情和基本面数据",
        "tools": [
            get_stock_daily_baostock,
            get_stock_weekly_baostock,
            get_stock_monthly_baostock,
            get_stock_valuation_baostock,
            get_stock_profit_baostock,
            get_stock_balance_baostock,
            get_stock_cashflow_baostock,
            get_hs300_constituents_baostock,
            get_sz50_constituents_baostock,
            get_zz500_constituents_baostock,
            get_stock_industry_baostock,
            get_trade_calendar_baostock,
            get_stock_info_baostock,
        ],
    },
}
