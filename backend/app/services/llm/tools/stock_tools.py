"""
LangChain Tools - 股票数据工具
"""
import logging
from typing import Optional, Annotated
from datetime import datetime, timedelta

from langchain_core.tools import tool

from app.services.data import (
    get_stock_service,
    get_index_service,
    get_fund_service,
    get_financial_service,
    get_market_service,
)
from app.services.stock_data import format_stock_data
from app.services.logging_manager import get_logger

logger = get_logger("stock_tools")


@tool
def get_stock_quote(stock_code: Annotated[str, "股票代码，如 000001、600000"]) -> str:
    """
    获取股票实时行情数据
    
    Args:
        stock_code: 股票代码
        
    Returns:
        股票实时行情字符串
    """
    try:
        stock = get_stock_service()
        quote = stock.get_quote(stock_code)
        
        if quote is None:
            return f"未能获取股票 {stock_code} 的实时行情数据"
        
        return format_stock_data("quote", quote)
    except Exception as e:
        logger.error(f"获取股票行情失败: {e}")
        return f"获取股票行情失败: {str(e)}"


@tool
def get_stock_daily(
    stock_code: Annotated[str, "股票代码"],
    days: Annotated[int, "获取天数，默认30天"] = 30
) -> str:
    """
    获取股票历史日线数据
    
    Args:
        stock_code: 股票代码
        days: 获取天数
        
    Returns:
        股票日线数据字符串
    """
    try:
        stock = get_stock_service()
        
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        df = stock.get_daily(stock_code, start_date, end_date)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的历史数据"
        
        return format_stock_data("daily", df, limit=days)
    except Exception as e:
        logger.error(f"获取日线数据失败: {e}")
        return f"获取日线数据失败: {str(e)}"


@tool
def get_index_quote(index_code: Annotated[str, "指数代码，如 000001、399001"]) -> str:
    """
    获取指数实时行情
    
    Args:
        index_code: 指数代码
        
    Returns:
        指数行情字符串
    """
    try:
        index = get_index_service()
        quote = index.get_quote(index_code)
        
        if quote is None:
            return f"未能获取指数 {index_code} 的行情数据"
        
        return format_stock_data("index", quote, index_name=index_code)
    except Exception as e:
        logger.error(f"获取指数行情失败: {e}")
        return f"获取指数行情失败: {str(e)}"


@tool
def get_fina_indicator(
    stock_code: Annotated[str, "股票代码"],
    periods: Annotated[int, "获取报告期数量，默认4个"] = 4
) -> str:
    """
    获取股票财务指标
    
    Args:
        stock_code: 股票代码
        periods: 获取报告期数量
        
    Returns:
        财务指标数据字符串
    """
    try:
        financial = get_financial_service()
        df = financial.get_fina_indicator(stock_code, periods)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的财务指标数据"
        
        return format_stock_data("financial", df)
    except Exception as e:
        logger.error(f"获取财务指标失败: {e}")
        return f"获取财务指标失败: {str(e)}"


@tool
def get_moneyflow(
    stock_code: Annotated[str, "股票代码"],
    days: Annotated[int, "获取天数，默认10天"] = 10
) -> str:
    """
    获取股票资金流向
    
    Args:
        stock_code: 股票代码
        days: 获取天数
        
    Returns:
        资金流向数据字符串
    """
    try:
        market = get_market_service()
        df = market.get_moneyflow(stock_code, days)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的资金流向数据"
        
        return format_stock_data("moneyflow", df)
    except Exception as e:
        logger.error(f"获取资金流向失败: {e}")
        return f"获取资金流向失败: {str(e)}"


@tool
def get_margin(
    stock_code: Annotated[str, "股票代码"],
    days: Annotated[int, "获取天数，默认10天"] = 10
) -> str:
    """
    获取融资融券数据
    
    Args:
        stock_code: 股票代码
        days: 获取天数
        
    Returns:
        融资融券数据字符串
    """
    try:
        market = get_market_service()
        df = market.get_margin(stock_code, days)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的融资融券数据"
        
        return format_stock_data("margin", df)
    except Exception as e:
        logger.error(f"获取融资融券失败: {e}")
        return f"获取融资融券失败: {str(e)}"


@tool
def get_leaderboard(date: Annotated[str, "日期，格式 YYYYMMDD，默认最新"]) -> str:
    """
    获取龙虎榜数据
    
    Args:
        date: 日期，格式 YYYYMMDD
        
    Returns:
        龙虎榜数据字符串
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        market = get_market_service()
        df = market.get_leaderboard(date)
        
        if df is None or df.empty:
            return f"未能获取 {date} 的龙虎榜数据"
        
        return format_stock_data("leaderboard", df)
    except Exception as e:
        logger.error(f"获取龙虎榜失败: {e}")
        return f"获取龙虎榜失败: {str(e)}"


@tool
def get_etf_spot(limit: Annotated[int, "返回数量，默认20"] = 20) -> str:
    """
    获取 ETF 实时行情
    
    Args:
        limit: 返回数量
        
    Returns:
        ETF 行情数据字符串
    """
    try:
        fund = get_fund_service()
        df = fund.get_etf_spot()
        
        if df is None or df.empty:
            return "未能获取 ETF 行情数据"
        
        return format_stock_data("etf", df, limit=limit)
    except Exception as e:
        logger.error(f"获取ETF行情失败: {e}")
        return f"获取ETF行情失败: {str(e)}"


@tool
def get_hsgt_moneyflow() -> str:
    """
    获取北向资金流向
    
    Returns:
        北向资金流向数据字符串
    """
    try:
        market = get_market_service()
        df = market.get_moneyflow_hsgt()
        
        if df is None or df.empty:
            return "未能获取北向资金流向数据"
        
        return format_stock_data("hsgt", df)
    except Exception as e:
        logger.error(f"获取北向资金流向失败: {e}")
        return f"获取北向资金流向失败: {str(e)}"


@tool
def get_industry_flow(limit: Annotated[int, "返回数量，默认10"] = 10) -> str:
    """
    获取行业资金流向
    
    Args:
        limit: 返回数量
        
    Returns:
        行业资金流向数据字符串
    """
    try:
        market = get_market_service()
        df = market.get_industry_flow(limit)
        
        if df is None or df.empty:
            return "未能获取行业资金流向数据"
        
        return format_stock_data("industry", df)
    except Exception as e:
        logger.error(f"获取行业资金流向失败: {e}")
        return f"获取行业资金流向失败: {str(e)}"


# ===== 新增的股票分析工具 =====

@tool
def get_stock_fundamentals(
    stock_code: Annotated[str, "股票代码，如 000001、600000"]
) -> str:
    """
    获取股票基本面数据
    
    Args:
        stock_code: 股票代码
        
    Returns:
        股票基本面数据字符串
    """
    try:
        stock_service = get_stock_service()
        # 获取基本面信息，包括公司概况、财务指标等
        fundamentals = stock_service.get_fundamentals(stock_code)
        
        if fundamentals is None:
            return f"未能获取股票 {stock_code} 的基本面数据"
        
        return format_stock_data("fundamentals", fundamentals)
    except Exception as e:
        logger.error(f"获取股票基本面失败: {e}")
        return f"获取股票基本面失败: {str(e)}"


@tool
def get_stock_financial(
    stock_code: Annotated[str, "股票代码，如 000001、600000"],
    statement_type: Annotated[str, "财务报表类型：balance_sheet, income_statement, cash_flow"] = "balance_sheet"
) -> str:
    """
    获取股票财务报表数据
    
    Args:
        stock_code: 股票代码
        statement_type: 财务报表类型
        
    Returns:
        股票财务报表数据字符串
    """
    try:
        financial_service = get_financial_service()
        financial_data = financial_service.get_financial_statements(
            stock_code, statement_type
        )
        
        if financial_data is None:
            return f"未能获取股票 {stock_code} 的{statement_type}财务数据"
        
        return format_stock_data("financial_statement", financial_data, statement_type=statement_type)
    except Exception as e:
        logger.error(f"获取股票财务数据失败: {e}")
        return f"获取股票财务数据失败: {str(e)}"


@tool
def get_stock_market_data(
    stock_code: Annotated[str, "股票代码，如 000001、600000"],
    data_type: Annotated[str, "数据类型：realtime, daily, weekly, monthly"] = "realtime"
) -> str:
    """
    获取股票市场数据
    
    Args:
        stock_code: 股票代码
        data_type: 数据类型
        
    Returns:
        股票市场数据字符串
    """
    try:
        stock_service = get_stock_service()
        
        if data_type == "realtime":
            data = stock_service.get_realtime_quote(stock_code)
        elif data_type == "daily":
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            data = stock_service.get_daily(stock_code, start_date, end_date)
        elif data_type == "weekly":
            data = stock_service.get_weekly(stock_code)
        elif data_type == "monthly":
            data = stock_service.get_monthly(stock_code)
        else:
            # 默认获取实时行情
            data = stock_service.get_realtime_quote(stock_code)
        
        if data is None:
            return f"未能获取股票 {stock_code} 的{data_type}市场数据"
        
        return format_stock_data("market_data", data, data_type=data_type)
    except Exception as e:
        logger.error(f"获取股票市场数据失败: {e}")
        return f"获取股票市场数据失败: {str(e)}"


@tool
def get_stock_technical(
    stock_code: Annotated[str, "股票代码，如 000001、600000"],
    indicators: Annotated[str, "技术指标列表，如 MACD,RSI,KDJ"] = "MACD,RSI,KDJ"
) -> str:
    """
    获取股票技术指标数据
    
    Args:
        stock_code: 股票代码
        indicators: 技术指标列表
        
    Returns:
        股票技术指标数据字符串
    """
    try:
        # 获取历史数据用于技术指标计算
        stock_service = get_stock_service()
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
        df = stock_service.get_daily(stock_code, start_date, end_date)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的历史数据用于技术指标计算"
        
        # 计算技术指标（这里简化处理，实际应该调用技术指标计算服务）
        technical_data = {
            "stock_code": stock_code,
            "indicators": indicators.split(","),
            "data_points": len(df),
            "latest_values": {
                "close": df.iloc[-1]['close'] if 'close' in df.columns else None,
                "ma5": df.iloc[-1]['ma5'] if 'ma5' in df.columns else None,
                "ma10": df.iloc[-1]['ma10'] if 'ma10' in df.columns else None,
                "ma20": df.iloc[-1]['ma20'] if 'ma20' in df.columns else None,
            }
        }
        
        return format_stock_data("technical", technical_data, indicators=indicators)
    except Exception as e:
        logger.error(f"获取股票技术指标失败: {e}")
        return f"获取股票技术指标失败: {str(e)}"


@tool
def get_stock_risk(
    stock_code: Annotated[str, "股票代码，如 000001、600000"],
    risk_type: Annotated[str, "风险类型：market, credit, liquidity, operational"] = "market"
) -> str:
    """
    获取股票风险指标数据
    
    Args:
        stock_code: 股票代码
        risk_type: 风险类型
        
    Returns:
        股票风险指标数据字符串
    """
    try:
        # 获取风险相关数据
        stock_service = get_stock_service()
        market_service = get_market_service()
        
        risk_data = {
            "stock_code": stock_code,
            "risk_type": risk_type,
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        
        # 根据风险类型获取不同的风险指标
        if risk_type == "market":
            # 市场风险：波动率、贝塔等
            quote = stock_service.get_quote(stock_code)
            if quote:
                risk_data["metrics"]["volatility"] = quote.get("volatility", 0)
                risk_data["metrics"]["beta"] = quote.get("beta", 1.0)
        elif risk_type == "liquidity":
            # 流动性风险：换手率、市值等
            quote = stock_service.get_quote(stock_code)
            if quote:
                risk_data["metrics"]["turnover_rate"] = quote.get("turnover_rate", 0)
                risk_data["metrics"]["market_cap"] = quote.get("market_cap", 0)
        
        # 获取市场整体风险指标作为参考
        market_data = market_service.get_market_risk_indicators()
        if market_data:
            risk_data["market_reference"] = market_data
        
        return format_stock_data("risk", risk_data, risk_type=risk_type)
    except Exception as e:
        logger.error(f"获取股票风险数据失败: {e}")
        return f"获取股票风险数据失败: {str(e)}"


@tool
def get_stock_news(
    stock_code: Annotated[str, "股票代码，如 000001、600000"],
    limit: Annotated[int, "新闻数量限制，默认10"] = 10,
    hours_back: Annotated[int, "查看最近多少小时的新闻，默认24"] = 24
) -> str:
    """
    获取股票相关新闻
    
    Args:
        stock_code: 股票代码
        limit: 新闻数量限制
        hours_back: 查看最近多少小时的新闻
        
    Returns:
        股票相关新闻数据字符串
    """
    try:
        # 这里我们需要从新闻聚合服务获取股票新闻
        # 由于没有直接的新闻服务接口，我们尝试使用现有的新闻聚合器
        from app.services.news.aggregator import get_news_aggregator
        
        aggregator = get_news_aggregator()
        if aggregator:
            news_list = aggregator.get_stock_news(
                symbol=stock_code,
                limit=limit,
                hours_back=hours_back
            )
            
            if not news_list:
                return f"未能获取股票 {stock_code} 的相关新闻"
            
            news_data = {
                "stock_code": stock_code,
                "news_count": len(news_list),
                "news_list": news_list,
                "query_time": datetime.now().isoformat(),
                "hours_back": hours_back
            }
            
            return format_stock_data("news", news_data, limit=limit, hours_back=hours_back)
        else:
            # 如果新闻聚合器不可用，返回提示信息
            return f"新闻服务暂不可用，无法获取股票 {stock_code} 的相关新闻"
    except Exception as e:
        logger.error(f"获取股票新闻失败: {e}")
        return f"获取股票新闻失败: {str(e)}"


# 导出所有工具
STOCK_TOOLS = [
    get_stock_quote,
    get_stock_daily,
    get_index_quote,
    get_fina_indicator,
    get_moneyflow,
    get_margin,
    get_leaderboard,
    get_etf_spot,
    get_hsgt_moneyflow,
    get_industry_flow,
    # 新增的股票分析工具
    get_stock_fundamentals,
    get_stock_financial,
    get_stock_market_data,
    get_stock_technical,
    get_stock_risk,
    get_stock_news,
]