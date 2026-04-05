"""
股票数据统一格式化模块
为 AI 提供中文标签的结构化文本
"""
import logging
from typing import Dict, Any, Optional, Union
import pandas as pd
from app.services.logging_manager import get_logger

logger = get_logger("stock_data.formatters")


def format_quote(data: Dict[str, Any]) -> str:
    """格式化实时行情"""
    if not data:
        return "无数据"
    
    try:
        return f"""股票代码: {data.get('ts_code', data.get('symbol', 'N/A'))}
股票名称: {data.get('name', 'N/A')}
当前价格: ¥{data.get('price', data.get('close', 'N/A'))}
涨跌幅度: {data.get('pct_chg', 'N/A')}%
涨跌金额: {data.get('change', 'N/A')}
今日开盘: ¥{data.get('open', 'N/A')}
昨日收盘: ¥{data.get('pre_close', 'N/A')}
今日最高: ¥{data.get('high', 'N/A')}
今日最低: ¥{data.get('low', 'N/A')}
成交量: {data.get('vol', data.get('volume', 'N/A'))}
成交额: {data.get('amount', 'N/A')}"""
    except Exception as e:
        logger.error(f"格式化行情失败: {e}")
        return str(data)


def format_daily(df: Union[pd.DataFrame, list], limit: int = 30) -> str:
    """格式化历史日线"""
    if df is None or (hasattr(df, 'empty') and df.empty) or not df:
        return "无数据"
    
    lines = ["日期\t\t开盘\t收盘\t涨跌幅\t成交量\t成交额"]
    
    try:
        if isinstance(df, list):
            data = df[-limit:]
            for row in data:
                date = row.get('trade_date', row.get('date', ''))
                if isinstance(date, str) and len(date) == 8:
                    date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                lines.append(f"{date}\t{row.get('open', 0):.2f}\t{row.get('close', 0):.2f}\t{row.get('pct_chg', 0):.2f}%\t{row.get('vol', 0):.0f}\t{row.get('amount', 0):.2f}")
        else:
            df = df.tail(limit)
            for _, row in df.iterrows():
                date = row.get('trade_date', '')
                if isinstance(date, str) and len(date) == 8:
                    date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                lines.append(f"{date}\t{row.get('open', 0):.2f}\t{row.get('close', 0):.2f}\t{row.get('pct_chg', 0):.2f}%\t{row.get('vol', 0):.0f}\t{row.get('amount', 0):.2f}")
    except Exception as e:
        logger.error(f"格式化日线失败: {e}")
        return "格式化失败"
    
    return "\n".join(lines)


def format_financial(data: Any) -> str:
    """格式化财务指标"""
    if not data:
        return "无数据"
    
    try:
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return "无数据"
            df = data.head(1)
            row = df.iloc[0]
            
            period = row.get('end_date', 'N/A')
            if isinstance(period, str) and len(period) == 8:
                period = f"{period[:4]}-{period[4:6]}-{period[6:]}"
            
            return f"""报告期: {period}
净资产收益率(ROE): {row.get('roe', 'N/A')}%
资产负债率: {row.get('debt_to_assets', 'N/A')}%
毛利率: {row.get('grossprofit_margin', 'N/A')}%
净利率: {row.get('netprofit_margin', 'N/A')}%
每股收益(EPS): {row.get('eps', 'N/A')}
每股净资产(BPS): {row.get('bps', 'N/A')}
营业收入增长率: {row.get('revenue_growth_yoy', 'N/A')}%
净利润增长率: {row.get('netprofit_growth_yoy', 'N/A')}%"""
        elif isinstance(data, dict):
            return f"""报告期: {data.get('end_date', 'N/A')}
净资产收益率(ROE): {data.get('roe', 'N/A')}%
资产负债率: {data.get('debt_to_assets', 'N/A')}%
毛利率: {data.get('grossprofit_margin', 'N/A')}%
净利率: {data.get('netprofit_margin', 'N/A')}%
每股收益(EPS): {data.get('eps', 'N/A')}
每股净资产(BPS): {data.get('bps', 'N/A')}"""
    except Exception as e:
        logger.error(f"格式化财务数据失败: {e}")
        return "格式化失败"
    
    return str(data)


def format_moneyflow(data: Any) -> str:
    """格式化资金流向"""
    if not data:
        return "无数据"
    
    try:
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return "无数据"
            df = data.head(5)
            
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
    except Exception as e:
        logger.error(f"格式化资金流向失败: {e}")
        return "格式化失败"
    
    return str(data)


def format_margin(data: Any) -> str:
    """格式化融资融券"""
    if not data:
        return "无数据"
    
    try:
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return "无数据"
            df = data.head(5)
            
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
    except Exception as e:
        logger.error(f"格式化融资融券失败: {e}")
        return "格式化失败"
    
    return str(data)


def format_leaderboard(data: Any) -> str:
    """格式化龙虎榜"""
    if not data:
        return "无数据"
    
    try:
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return "无数据"
            df = data.head(10)
            
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
    except Exception as e:
        logger.error(f"格式化龙虎榜失败: {e}")
        return "格式化失败"
    
    return str(data)


def format_etf(data: Any, limit: int = 20) -> str:
    """格式化ETF行情"""
    if not data:
        return "无数据"
    
    try:
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return "无数据"
            df = data.head(limit)
            
            lines = ["代码\t名称\t最新价\t涨跌幅\t成交量\t成交额"]
            
            for _, row in df.iterrows():
                code = row.get('ts_code', row.get('symbol', ''))
                name = row.get('name', '')
                close = row.get('close', row.get('price', 0)) or 0
                pct = row.get('pct_chg', 0) or 0
                vol = row.get('vol', 0) or 0
                amount = row.get('amount', 0) or 0
                
                lines.append(f"{code}\t{name}\t{close:.2f}\t{pct:.2f}%\t{vol:.0f}\t{amount:.2f}")
            
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"格式化ETF失败: {e}")
        return "格式化失败"
    
    return str(data)


def format_hsgt(data: Any) -> str:
    """格式化北向资金"""
    if not data:
        return "无数据"
    
    try:
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return "无数据"
            df = data.head(10)
            
            lines = ["日期\t\t沪股通\t深股通\t北向合计"]
            
            for _, row in df.iterrows():
                date = row.get('trade_date', '')
                if isinstance(date, str) and len(date) == 8:
                    date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                
                hgt = row.get('sh_net_inflow', row.get('hgt_net_inflow', 0)) or 0
                sgt = row.get('sz_net_inflow', row.get('sgt_net_inflow', 0)) or 0
                total = row.get('north_net_inflow', hgt + sgt) or 0
                
                lines.append(f"{date}\t{hgt:.2f}\t{sgt:.2f}\t{total:.2f}")
            
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"格式化北向资金失败: {e}")
        return "格式化失败"
    
    return str(data)


def format_industry(data: Any) -> str:
    """格式化行业资金流"""
    if not data:
        return "无数据"
    
    try:
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return "无数据"
            df = data.head(10)
            
            lines = ["行业\t\t主力净流入\t净流入占比"]
            
            for _, row in df.iterrows():
                industry = row.get('industry', row.get('name', ''))
                main = row.get('net_main_inflow', row.get('main_inflow', 0)) or 0
                ratio = row.get('net_inflow_ratio', row.get('ratio', 0)) or 0
                
                lines.append(f"{industry}\t{main:.2f}\t{ratio:.2f}%")
            
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"格式化行业资金流失败: {e}")
        return "格式化失败"
    
    return str(data)


def format_index(data: Any, index_name: str = "") -> str:
    """格式化指数行情"""
    if not data:
        return "无数据"
    
    try:
        if isinstance(data, dict):
            name = data.get('name', index_name or '指数')
            return f"""指数名称: {name}
当前点位: {data.get('close', data.get('nowpri', 'N/A'))}
涨跌幅: {data.get('pct_chg', data.get('increPer', 'N/A'))}%
涨跌额: {data.get('change', data.get('increase', 'N/A'))}
今日开盘: {data.get('open', data.get('openPri', 'N/A'))}
昨日收盘: {data.get('pre_close', data.get('yesPri', 'N/A'))}
今日最高: {data.get('high', data.get('highPri', 'N/A'))}
今日最低: {data.get('low', data.get('lowPri', 'N/A'))}
成交量: {data.get('vol', data.get('dealNum', 'N/A'))}
成交额: {data.get('amount', data.get('dealPri', 'N/A'))}"""
    except Exception as e:
        logger.error(f"格式化指数失败: {e}")
        return "格式化失败"
    
    return str(data)


# 统一格式化入口
FORMATTERS = {
    "quote": format_quote,
    "daily": format_daily,
    "financial": format_financial,
    "moneyflow": format_moneyflow,
    "margin": format_margin,
    "leaderboard": format_leaderboard,
    "etf": format_etf,
    "hsgt": format_hsgt,
    "industry": format_industry,
    "index": format_index,
}


def format_stock_data(data_type: str, data: Any, **kwargs) -> str:
    """
    统一格式化入口
    
    Args:
        data_type: 数据类型 (quote/daily/financial/moneyflow/margin/leaderboard/etf/hsgt/industry/index)
        data: 原始数据
        **kwargs: 其他参数 (如 limit, index_name)
    
    Returns:
        格式化后的字符串
    """
    formatter = FORMATTERS.get(data_type)
    if not formatter:
        return str(data) if data else "无数据"
    
    if data_type == "daily":
        return formatter(data, kwargs.get("limit", 30))
    elif data_type == "etf":
        return formatter(data, kwargs.get("limit", 20))
    elif data_type == "index":
        return formatter(data, kwargs.get("index_name", ""))
    
    return formatter(data)
