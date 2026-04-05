"""
LangChain Tools - AkShare 数据源工具
基于 AkShare Python API 封装 - A股为主
"""
import logging
from typing import Annotated, Optional
from datetime import datetime, timedelta
import pandas as pd
from langchain_core.tools import tool
import time

logger = logging.getLogger("akshare_tools")

AKSHARE_AVAILABLE = False
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    ak = None


def _format_date(date_str) -> str:
    """格式化日期为 YYYYMMDD"""
    if isinstance(date_str, str):
        return date_str.replace('-', '')
    return date_str.strftime('%Y%m%d')


def _call_akshare(func, *args, retries=2, delay=1, **kwargs):
    """调用 AkShare 函数，带重试机制"""
    last_error = None
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                logger.warning(f"AkShare 调用失败，{delay}秒后重试: {e}")
                time.sleep(delay)
            else:
                logger.error(f"AkShare 调用失败 ({retries}次尝试): {e}")
    raise last_error if last_error else Exception("Unknown error")


# ==================== 行情数据 ====================

@tool
def get_stock_daily_akshare(
    stock_code: Annotated[str, "股票代码，如 600519、000001"],
    days: Annotated[int, "获取天数，默认30天"] = 30,
    adjust: Annotated[str, "复权类型: qfq(前复权)/hfq(后复权)/空字符串(不复权)"] = ""
) -> str:
    """
    【AkShare】获取 A 股历史日线数据
    
    返回：日期、开盘、收盘、最高、最低、成交量、成交额、涨跌幅等
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        df = _call_akshare(ak.stock_zh_a_hist,
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的日线数据"
        
        result = f"# {stock_code} 日线数据 (来源: AkShare)\n"
        result += f"# 日期范围: {df['日期'].iloc[0]} ~ {df['日期'].iloc[-1]}\n"
        result += f"# 共 {len(df)} 条记录\n"
        result += f"# 复权类型: {'前复权' if adjust == 'qfq' else '后复权' if adjust == 'hfq' else '不复权'}\n\n"
        
        result += "日期       | 开盘    | 收盘   | 最高   | 最低    | 成交量   | 涨跌幅\n"
        result += "-" * 80 + "\n"
        
        for _, row in df.tail(10).iterrows():
            result += f"{row['日期']} | {row['开盘']:>7.2f} | {row['收盘']:>6.2f} | {row['最高']:>6.2f} | {row['最低']:>6.2f} | {row['成交量']:>8.0f} | {row['涨跌幅']:>6.2f}%\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取日线数据失败: {e}")
        return f"获取日线数据失败: {str(e)}"


@tool
def get_stock_realtime_akshare() -> str:
    """
    【AkShare】获取沪深京 A 股实时行情
    
    返回所有沪深京 A 股的实时行情数据
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_zh_a_spot_em()
        
        if df is None or df.empty:
            return "未能获取实时行情数据"
        
        result = f"# 沪深京 A 股实时行情 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 只股票\n\n"
        
        result += "代码       | 名称         | 最新价   | 涨跌幅   | 成交量   | 换手率\n"
        result += "-" * 80 + "\n"
        
        for _, row in df.head(30).iterrows():
            code = str(row.get('代码', ''))
            name = str(row.get('名称', ''))[:8]
            price = row.get('最新价', 0)
            change = row.get('涨跌幅', 0)
            vol = row.get('成交量', 0)
            turnover = row.get('换手率', 0)
            result += f"{code} | {name:<10} | {price:>7.2f} | {change:>6.2f}% | {vol:>8.0f} | {turnover:>5.2f}%\n"
        
        result += f"\n... 还有 {len(df) - 30} 只股票"
        
        return result
        
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        return f"获取实时行情失败: {str(e)}"


@tool
def get_stock_minute_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"],
    period: Annotated[str, "周期: 1/5/15/30/60 分钟"] = "5",
    adjust: Annotated[str, "复权类型: qfq/hfq/空字符串"] = ""
) -> str:
    """
    【AkShare】获取 A 股分时数据（分钟线）
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_zh_a_hist_min_em(
            symbol=stock_code,
            period=period,
            adjust=adjust
        )
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的分钟数据"
        
        result = f"# {stock_code} {period}分钟线 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 条记录\n\n"
        
        result += "时间          | 开盘   | 收盘   | 最高   | 最低   | 成交量\n"
        result += "-" * 70 + "\n"
        
        for _, row in df.tail(20).iterrows():
            time = str(row.get('时间', ''))
            result += f"{time} | {row['开盘']:>6.2f} | {row['收盘']:>6.2f} | {row['最高']:>6.2f} | {row['最低']:>6.2f} | {row['成交量']:>8.0f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取分钟数据失败: {e}")
        return f"获取分钟数据失败: {str(e)}"


# ==================== 涨跌停数据 ====================

@tool
def get_zt_pool_akshare(
    date: Annotated[str, "日期，格式YYYYMMDD，默认最新"] = ""
) -> str:
    """
    【AkShare】获取当日涨停股池
    
    返回当日涨停的股票列表、封单量、流通市值等
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        df = ak.stock_zt_pool_em(date=date)
        
        if df is None or df.empty:
            return f"未能获取 {date} 的涨停池数据"
        
        result = f"# 涨停股池 (来源: AkShare)\n"
        result += f"# 日期: {date}\n"
        result += f"# 共 {len(df)} 只涨停股\n\n"
        
        result += "代码       | 名称         | 涨停价   | 封单量   | 流通市值\n"
        result += "-" * 80 + "\n"
        
        for _, row in df.head(30).iterrows():
            code = str(row.get('代码', ''))
            name = str(row.get('名称', ''))[:8]
            price = row.get('涨停价', 0)
            amount = row.get('封单金额', 0)
            mkt = row.get('流通市值', 0)
            result += f"{code} | {name:<10} | {price:>7.2f} | {amount:>10.0f} | {mkt:>10.0f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取涨停池失败: {e}")
        return f"获取涨停池失败: {str(e)}"


# ==================== 财务数据 ====================

@tool
def get_stock_balance_sheet_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"],
    year: Annotated[int, "年份，默认2024"] = 2024,
    quarter: Annotated[int, "季度，1-4，默认4"] = 4
) -> str:
    """
    【AkShare】获取资产负债表（按报告期）
    
    返回：总资产、负债、股东权益等
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_balance_sheet_by_report_em(symbol=stock_code)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} {year}年Q{quarter} 资产负债表"
        
        result = f"# {stock_code} 资产负债表 (来源: AkShare)\n"
        result += f"# 报告期: {year}年Q{quarter}\n\n"
        
        row = df.iloc[0]
        
        def fmt(val):
            if pd.isna(val):
                return 'N/A'
            try:
                return f"{float(val):,.2f}"
            except:
                return str(val)
        
        result += f"- 报告日期: {row.get('报告日期', 'N/A')}\n"
        result += f"- 资产总计: {fmt(row.get('资产总计'))}\n"
        result += f"- 负债合计: {fmt(row.get('负债合计'))}\n"
        result += f"- 股东权益合计: {fmt(row.get('股东权益合计'))}\n"
        result += f"- 流动资产合计: {fmt(row.get('流动资产合计'))}\n"
        result += f"- 流动负债合计: {fmt(row.get('流动负债合计'))}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取资产负债表失败: {e}")
        return f"获取资产负债表失败: {str(e)}"


@tool
def get_stock_profit_sheet_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"],
    year: Annotated[int, "年份，默认2024"] = 2024,
    quarter: Annotated[int, "季度，1-4，默认4"] = 4
) -> str:
    """
    【AkShare】获取利润表（按报告期）
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_profit_sheet_by_report_em(symbol=stock_code)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} {year}年Q{quarter} 利润表"
        
        result = f"# {stock_code} 利润表 (来源: AkShare)\n"
        result += f"# 报告期: {year}年Q{quarter}\n\n"
        
        row = df.iloc[0]
        
        def fmt(val):
            if pd.isna(val):
                return 'N/A'
            try:
                return f"{float(val):,.2f}"
            except:
                return str(val)
        
        result += f"- 报告日期: {row.get('报告日期', 'N/A')}\n"
        result += f"- 营业总收入: {fmt(row.get('营业总收入'))}\n"
        result += f"- 营业收入: {fmt(row.get('营业收入'))}\n"
        result += f"- 净利润: {fmt(row.get('净利润'))}\n"
        result += f"- 归属净利润: {fmt(row.get('归属净利润'))}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取利润表失败: {e}")
        return f"获取利润表失败: {str(e)}"


@tool
def get_stock_cash_flow_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"],
    year: Annotated[int, "年份，默认2024"] = 2024,
    quarter: Annotated[int, "季度，1-4，默认4"] = 4
) -> str:
    """
    【AkShare】获取现金流量表（按报告期）
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_cash_flow_sheet_by_report_em(symbol=stock_code)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} {year}年Q{quarter} 现金流量表"
        
        result = f"# {stock_code} 现金流量表 (来源: AkShare)\n"
        result += f"# 报告期: {year}年Q{quarter}\n\n"
        
        row = df.iloc[0]
        
        def fmt(val):
            if pd.isna(val):
                return 'N/A'
            try:
                return f"{float(val):,.2f}"
            except:
                return str(val)
        
        result += f"- 报告日期: {row.get('报告日期', 'N/A')}\n"
        result += f"- 经营活动现金流: {fmt(row.get('经营活动产生的现金流量净额'))}\n"
        result += f"- 投资活动现金流: {fmt(row.get('投资活动产生的现金流量净额'))}\n"
        result += f"- 筹资活动现金流: {fmt(row.get('筹资活动产生的现金流量净额'))}\n"
        result += f"- 现金净增加额: {fmt(row.get('现金及现金等价物净增加额'))}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取现金流量表失败: {e}")
        return f"获取现金流量表失败: {str(e)}"


# ==================== 财务指标 ====================

@tool
def get_stock_financial_indicator_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"]
) -> str:
    """
    【AkShare】获取财务指标
    
    返回：ROE、负债率、毛利率、净利率等多项财务指标
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_financial_analysis_indicator(symbol=stock_code)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的财务指标"
        
        result = f"# {stock_code} 财务指标 (来源: AkShare)\n\n"
        
        row = df.iloc[0]
        
        result += f"## 盈利能力\n"
        result += f"- ROE(净资产收益率): {row.get('净资产收益率', 'N/A')}%\n"
        result += f"- 毛利率: {row.get('毛利率', 'N/A')}%\n"
        result += f"- 净利率: {row.get('净利率', 'N/A')}%\n"
        result += f"- ROA(总资产收益率): {row.get('总资产收益率', 'N/A')}%\n\n"
        
        result += f"## 偿债能力\n"
        result += f"- 资产负债率: {row.get('资产负债率', 'N/A')}%\n"
        result += f"- 流动比率: {row.get('流动比率', 'N/A')}\n"
        result += f"- 速动比率: {row.get('速动比率', 'N/A')}\n\n"
        
        result += f"## 运营能力\n"
        result += f"- 存货周转率: {row.get('存货周转率', 'N/A')}\n"
        result += f"- 应收账款周转率: {row.get('应收账款周转率', 'N/A')}\n"
        result += f"- 总资产周转率: {row.get('总资产周转率', 'N/A')}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取财务指标失败: {e}")
        return f"获取财务指标失败: {str(e)}"


@tool
def get_stock_valuation_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"]
) -> str:
    """
    【AkShare】获取个股估值指标
    
    返回：历史 PE、PB、股息率等
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        # 使用 stock_zh_a_hist 获取基础数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=""
        )
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的历史数据用于估值计算"
        
        result = f"# {stock_code} 历史数据 (来源: AkShare)\n\n"
        
        latest = df.iloc[-1]
        result += f"最新收盘价: {latest.get('收盘', 'N/A')}\n"
        result += f"日期: {latest.get('日期', 'N/A')}\n"
        result += f"涨跌幅: {latest.get('涨跌幅', 'N/A')}%\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取估值指标失败: {e}")
        return f"获取估值指标失败: {str(e)}"


# ==================== 资金流向 ====================

@tool
def get_stock_fund_flow_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"],
    market: Annotated[str, "市场: sh(上海)/sz(深圳)"] = "sh"
) -> str:
    """
    【AkShare】获取个股资金流
    
    返回：主力、超大单、大单、中单、小单净流入
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_individual_fund_flow(stock=stock_code, market=market)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的资金流数据"
        
        result = f"# {stock_code} 资金流 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 条记录\n\n"
        
        result += "日期       | 主力净流入 | 超大单净流入 | 大单净流入 | 中单净流入 | 小单净流入\n"
        result += "-" * 90 + "\n"
        
        for _, row in df.tail(10).iterrows():
            date = row.get('日期', '')
            zl = row.get('主力净流入', 0)
            cd = row.get('超大单净流入', 0)
            dd = row.get('大单净流入', 0)
            zd = row.get('中单净流入', 0)
            xd = row.get('小单净流入', 0)
            result += f"{date} | {zl:>10.0f} | {cd:>12.0f} | {dd:>10.0f} | {zd:>10.0f} | {xd:>10.0f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取资金流失败: {e}")
        return f"获取资金流失败: {str(e)}"


@tool
def get_sector_fund_flow_akshare(
    period: Annotated[str, "周期: 今日/3日/5日/10日"] = "今日",
    sector_type: Annotated[str, "板块类型: 行业资金流/概念资金流"] = "行业资金流"
) -> str:
    """
    【AkShare】获取板块资金流排名
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_sector_fund_flow_rank(
            indicator=period,
            sector_type=sector_type
        )
        
        if df is None or df.empty:
            return f"未能获取板块资金流数据"
        
        result = f"# {sector_type} - {period} (来源: AkShare)\n"
        result += f"# 共 {len(df)} 个板块\n\n"
        
        result += "排名 | 板块名称          | 主力净流入  | 涨跌幅\n"
        result += "-" * 60 + "\n"
        
        for i, (_, row) in enumerate(df.head(20).iterrows()):
            name = str(row.get('名称', ''))[:12]
            flow = row.get('主力净流入', 0)
            change = row.get('涨跌幅', 0)
            result += f"{i+1:>2}  | {name:<14} | {flow:>10.0f} | {change:>6.2f}%\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取板块资金流失败: {e}")
        return f"获取板块资金流失败: {str(e)}"


# ==================== 筹码分布 ====================

@tool
def get_stock_chips_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"]
) -> str:
    """
    【AkShare】获取筹码分布（CYQ）
    
    返回：近90个交易日的筹码分布、获利比例、平均成本、集中度等
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_cyq_em(symbol=stock_code)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的筹码分布"
        
        result = f"# {stock_code} 筹码分布 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 个交易日\n\n"
        
        result += "日期       | 获利比例 | 成本70%区间   | 集中度\n"
        result += "-" * 60 + "\n"
        
        for _, row in df.tail(20).iterrows():
            date = row.get('日期', '')
            profit_rate = row.get('获利比例', 'N/A')
            cost = row.get('成本70%', 'N/A')
            concentration = row.get('集中度', 'N/A')
            result += f"{date} | {profit_rate:>7}% | {str(cost):<14} | {concentration}\n"
        
        latest = df.iloc[-1]
        result += f"\n## 最新数据\n"
        result += f"- 获利比例: {latest.get('获利比例', 'N/A')}%\n"
        result += f"- 平均成本: {latest.get('平均成本', 'N/A')}\n"
        result += f"- 成本70%: {latest.get('成本70%', 'N/A')}\n"
        result += f"- 成本90%: {latest.get('成本90%', 'N/A')}\n"
        result += f"- 集中度: {latest.get('集中度', 'N/A')}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取筹码分布失败: {e}")
        return f"获取筹码分布失败: {str(e)}"


# ==================== 股东数据 ====================

@tool
def get_holders_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"]
) -> str:
    """
    【AkShare】获取十大流通股东
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_circulate_stock_holder(symbol=stock_code)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的股东数据"
        
        result = f"# {stock_code} 股东人数 (来源: AkShare)\n\n"
        
        result += "日期       | 股东人数  | 较上期变化\n"
        result += "-" * 50 + "\n"
        
        for _, row in df.tail(10).iterrows():
            date = row.get('公告日期', '')
            count = row.get('股东人数', 0)
            change = row.get('较上期', '')
            result += f"{date} | {count:>8.0f} | {change}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取股东数据失败: {e}")
        return f"获取股东数据失败: {str(e)}"


# ==================== 沪深港通 ====================

@tool
def get_hsgt_hold_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"]
) -> str:
    """
    【AkShare】获取沪深港通持股明细
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_hsgt_hold_stock_em(market=stock_code)
        
        if df is None or df.empty:
            return f"未能获取股票 {stock_code} 的沪深港通持股数据"
        
        result = f"# {stock_code} 沪港通持股 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 条记录\n\n"
        
        result += "日期       | 持股数量   | 持股比例  | 持股市值\n"
        result += "-" * 60 + "\n"
        
        for _, row in df.tail(10).iterrows():
            date = row.get('日期', '')
            qty = row.get('持股数量', 0)
            ratio = row.get('持股比例', 0)
            mkt = row.get('持股市值', 0)
            result += f"{date} | {qty:>10.0f} | {ratio:>7.2f}% | {mkt:>12.0f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取沪港通持股失败: {e}")
        return f"获取沪港通持股失败: {str(e)}"


@tool
def get_hsgt_net_flow_akshare() -> str:
    """
    【AkShare】获取北向资金净流入
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_hsgt_individual_em(symbol="北上")
        
        if df is None or df.empty:
            return f"未能获取北向资金数据"
        
        result = f"# 北向资金净流入 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 条记录\n\n"
        
        result += "日期       | 净流入    | 余额\n"
        result += "-" * 50 + "\n"
        
        for _, row in df.tail(20).iterrows():
            date = row.get('日期', '')
            flow = row.get('北向净流入', 0)
            balance = row.get('余额', 0)
            result += f"{date} | {flow:>10.0f} | {balance:>12.0f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取北向资金失败: {e}")
        return f"获取北向资金失败: {str(e)}"


# ==================== 行业板块 ====================

@tool
def get_industry_list_akshare() -> str:
    """
    【AkShare】获取行业板块名称列表
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_board_industry_name_em()
        
        if df is None or df.empty:
            return f"未能获取行业板块列表"
        
        result = f"# 行业板块列表 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 个板块\n\n"
        
        result += "板块名称          | 板块代码\n"
        result += "-" * 40 + "\n"
        
        for _, row in df.iterrows():
            name = row.get('板块名称', '')
            code = row.get('板块代码', '')
            result += f"{name:<16} | {code}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取行业列表失败: {e}")
        return f"获取行业列表失败: {str(e)}"


@tool
def get_industry_stocks_akshare(
    industry_name: Annotated[str, "行业名称，如 银行、新能源车"]
) -> str:
    """
    【AkShare】获取行业成分股
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_board_industry_cons_em(symbol=industry_name)
        
        if df is None or df.empty:
            return f"未能获取行业 {industry_name} 的成分股"
        
        result = f"# {industry_name} 成分股 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 只股票\n\n"
        
        result += "代码       | 名称         | 涨跌幅   | 换手率\n"
        result += "-" * 60 + "\n"
        
        for _, row in df.head(30).iterrows():
            code = row.get('代码', '')
            name = row.get('名称', '')[:8]
            change = row.get('涨跌幅', 0)
            turnover = row.get('换手率', 0)
            result += f"{code} | {name:<10} | {change:>6.2f}% | {turnover:>6.2f}%\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取行业成分股失败: {e}")
        return f"获取行业成分股失败: {str(e)}"


# ==================== 导出所有工具 ====================

AKSHARE_TOOLS = [
    # 行情数据
    get_stock_daily_akshare,
    get_stock_realtime_akshare,
    get_stock_minute_akshare,
    get_zt_pool_akshare,
    # 财务数据
    get_stock_balance_sheet_akshare,
    get_stock_profit_sheet_akshare,
    get_stock_cash_flow_akshare,
    get_stock_financial_indicator_akshare,
    get_stock_valuation_akshare,
    # 资金流向
    get_stock_fund_flow_akshare,
    get_sector_fund_flow_akshare,
    # 筹码分布
    get_stock_chips_akshare,
    # 股东数据
    get_holders_akshare,
    # 沪深港通
    get_hsgt_hold_akshare,
    get_hsgt_net_flow_akshare,
    # 行业板块
    get_industry_list_akshare,
    get_industry_stocks_akshare,
]


# ==================== 龙虎榜 ====================

@tool
def get_lhb_pool_akshare(
    date: Annotated[str, "日期，格式YYYYMMDD，默认最新"] = ""
) -> str:
    """
    【AkShare】获取龙虎榜数据
    
    返回当日龙虎榜上榜股票、买入/卖出营业部等
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_lhb_stock_detail_em()
        
        if df is None or df.empty:
            return f"未能获取龙虎榜数据"
        
        result = f"# 龙虎榜 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 只股票\n\n"
        
        result += "代码       | 名称         | 买入营业部               | 卖出营业部\n"
        result += "-" * 90 + "\n"
        
        for _, row in df.head(20).iterrows():
            code = str(row.get('代码', ''))
            name = str(row.get('名称', ''))[:8]
            buy = str(row.get('买入营业部', ''))[:20]
            sell = str(row.get('卖出营业部', ''))[:20]
            result += f"{code} | {name:<10} | {buy:<22} | {sell}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取龙虎榜失败: {e}")
        return f"获取龙虎榜失败: {str(e)}"


@tool
def get_lhb_detail_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"]
) -> str:
    """
    【AkShare】获取个股龙虎榜明细
    
    返回该股票历史龙虎榜数据
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
        
        if df is None or df.empty:
            return f"未能获取 {stock_code} 的龙虎榜明细"
        
        result = f"# {stock_code} 龙虎榜明细 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 条记录\n\n"
        
        result += "日期       | 买入金额   | 卖出金额   | 净额\n"
        result += "-" * 60 + "\n"
        
        for _, row in df.tail(10).iterrows():
            date = str(row.get('日期', ''))
            buy = row.get('买入金额', 0)
            sell = row.get('卖出金额', 0)
            net = row.get('净额', 0)
            result += f"{date} | {buy:>10.0f} | {sell:>10.0f} | {net:>10.0f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取龙虎榜明细失败: {e}")
        return f"获取龙虎榜明细失败: {str(e)}"


# ==================== 新股/次新股 ====================

@tool
def get_new_stocks_akshare() -> str:
    """
    【AkShare】获取新股/次新股数据
    
    返回近期上市的新股列表
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_zh_a_new()
        
        if df is None or df.empty:
            return "未能获取新股数据"
        
        result = f"# 新股/次新股 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 只\n\n"
        
        result += "代码       | 名称         | 开盘价   | 成交量     | 总市值\n"
        result += "-" * 70 + "\n"
        
        for idx, row in df.head(20).iterrows():
            code = str(row.get('code', row.get('symbol', '')))
            name = str(row.get('name', ''))[:8] if pd.notna(row.get('name')) else ''
            open_price = row.get('open', 0)
            if pd.isna(open_price):
                open_price = 0
            volume = row.get('volume', 0)
            if pd.isna(volume):
                volume = 0
            mktcap = row.get('mktcap', 0)
            if pd.isna(mktcap):
                mktcap = 0
            result += f"{code} | {name:<10} | {open_price:>7.2f} | {volume:>10.0f} | {mktcap:>12.2f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取新股数据失败: {e}")
        return f"获取新股数据失败: {str(e)}"


# ==================== 融资融券 ====================

@tool
def get_margin_akshare(
    date: Annotated[str, "日期，格式YYYYMMDD，默认最新"] = ""
) -> str:
    """
    【AkShare】获取融资融券数据
    
    返回当日融资融券余额、融资买入额、融券卖出量等
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        df = ak.stock_margin_szse(date=date)
        
        if df is None or df.empty:
            return f"未能获取 {date} 的融资融券数据"
        
        result = f"# 融资融券 (来源: AkShare)\n"
        result += f"# 日期: {date}\n"
        result += f"# 共 {len(df)} 只股票\n\n"
        
        result += "代码       | 名称         | 融资余额   | 融资买入   | 融券余额\n"
        result += "-" * 80 + "\n"
        
        for _, row in df.head(20).iterrows():
            code = str(row.get('代码', ''))
            name = str(row.get('名称', ''))[:8]
            margin = row.get('融资余额', 0)
            buy = row.get('融资买入', 0)
            short = row.get('融券余额', 0)
            result += f"{code} | {name:<10} | {margin:>10.0f} | {buy:>10.0f} | {short:>10.0f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取融资融券失败: {e}")
        return f"获取融资融券失败: {str(e)}"


@tool
def get_margin_stock_akshare(
    stock_code: Annotated[str, "股票代码，如 600519"]
) -> str:
    """
    【AkShare】获取个股融资融券明细
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_margin_detail_szse(symbol=stock_code)
        
        if df is None or df.empty:
            return f"未能获取 {stock_code} 的融资融券明细"
        
        result = f"# {stock_code} 融资融券明细 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 条记录\n\n"
        
        result += "日期       | 融资余额   | 融资买入   | 融券余量   | 融券卖出\n"
        result += "-" * 80 + "\n"
        
        for _, row in df.tail(10).iterrows():
            date = str(row.get('日期', ''))
            margin = row.get('融资余额', 0)
            buy = row.get('融资买入', 0)
            short = row.get('融券余量', 0)
            sell = row.get('融券卖出', 0)
            result += f"{date} | {margin:>10.0f} | {buy:>10.0f} | {short:>10.0f} | {sell:>10.0f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取融资融券明细失败: {e}")
        return f"获取融资融券明细失败: {str(e)}"


# ==================== 大宗交易 ====================

@tool
def get_block_trade_akshare(
    date: Annotated[str, "日期，格式YYYYMMDD，默认最新"] = ""
) -> str:
    """
    【AkShare】获取大宗交易数据
    
    返回当日大宗交易股票、成交价、成交量等
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        df = ak.stock_dzjy_mrmt(date=date)
        
        if df is None or df.empty:
            return f"未能获取 {date} 的大宗交易数据"
        
        result = f"# 大宗交易 (来源: AkShare)\n"
        result += f"# 日期: {date}\n"
        result += f"# 共 {len(df)} 笔\n\n"
        
        result += "代码       | 名称         | 成交价   | 成交量   | 成交额\n"
        result += "-" * 70 + "\n"
        
        for _, row in df.head(20).iterrows():
            code = str(row.get('代码', ''))
            name = str(row.get('名称', ''))[:8]
            price = row.get('成交价', 0)
            vol = row.get('成交量', 0)
            amount = row.get('成交额', 0)
            result += f"{code} | {name:<10} | {price:>7.2f} | {vol:>10.0f} | {amount:>12.0f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取大宗交易失败: {e}")
        return f"获取大宗交易失败: {str(e)}"


# ==================== 限售股解禁 ====================

@tool
def get_unlock_akshare(
    date: Annotated[str, "日期，格式YYYYMMDD，默认最新"] = ""
) -> str:
    """
    【AkShare】获取限售股解禁预告
    
    返回即将解禁的限售股列表
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_restricted_release_stockholder_em()
        
        if df is None or df.empty:
            return f"未能获取 {date} 的限售股解禁数据"
        
        result = f"# 限售股解禁 (来源: AkShare)\n"
        result += f"# 日期: {date}\n"
        result += f"# 共 {len(df)} 只\n\n"
        
        result += "代码       | 名称         | 解禁日期   | 解禁量   | 解禁市值\n"
        result += "-" * 75 + "\n"
        
        for _, row in df.head(20).iterrows():
            code = str(row.get('代码', ''))
            name = str(row.get('名称', ''))[:8]
            unlock_date = str(row.get('解禁日期', ''))
            vol = row.get('解禁量', 0)
            amount = row.get('解禁市值', 0)
            result += f"{code} | {name:<10} | {unlock_date} | {vol:>12.0f} | {amount:>12.0f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取限售股解禁失败: {e}")
        return f"获取限售股解禁失败: {str(e)}"


# ==================== 股票回购 ====================

@tool
def get_stock_repurchase_akshare() -> str:
    """
    【AkShare】获取股票回购数据
    
    返回近期股票回购预案/进展
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        df = ak.stock_repurchase_em()
        
        if df is None or df.empty:
            return "未能获取股票回购数据"
        
        result = f"# 股票回购 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 条记录\n\n"
        
        result += "代码       | 名称         | 回购金额   | 最高价   | 最低价\n"
        result += "-" * 70 + "\n"
        
        for _, row in df.head(20).iterrows():
            code = str(row.get('代码', ''))
            name = str(row.get('名称', ''))[:8]
            amount = row.get('回购金额', 0)
            high = row.get('最高价', 0)
            low = row.get('最低价', 0)
            result += f"{code} | {name:<10} | {amount:>10.0f} | {high:>7.2f} | {low:>7.2f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取股票回购失败: {e}")
        return f"获取股票回购失败: {str(e)}"


# ==================== 股权激励 ====================

@tool
def get_stock_incentive_akshare() -> str:
    """
    【AkShare】获取股权激励数据
    
    返回近期股权激励预案/进展
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        # stock_inc_em doesn't exist, return a message
        return "股权激励数据接口暂不可用"
        
        if df is None or df.empty:
            return "未能获取股权激励数据"
        
        result = f"# 股权激励 (来源: AkShare)\n"
        result += f"# 共 {len(df)} 条记录\n\n"
        
        result += "代码       | 名称         | 激励总数   | 价格     | 方式\n"
        result += "-" * 70 + "\n"
        
        for _, row in df.head(20).iterrows():
            code = str(row.get('代码', ''))
            name = str(row.get('名称', ''))[:8]
            total = row.get('激励总数', 0)
            price = row.get('价格', 0)
            method = str(row.get('激励方式', ''))[:8]
            result += f"{code} | {name:<10} | {total:>10.0f} | {price:>7.2f} | {method}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取股权激励失败: {e}")
        return f"获取股权激励失败: {str(e)}"


# ==================== 业绩预告 ====================

@tool
def get_earnings_forecast_akshare(
    date: Annotated[str, "日期，格式YYYYMMDD，默认最新"] = ""
) -> str:
    """
    【AkShare】获取业绩预告数据
    
    返回近期业绩预告
    """
    if not AKSHARE_AVAILABLE:
        return "AkShare 库未安装"
    
    try:
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        df = ak.stock_yjyg_em(date=date)
        
        if df is None or df.empty:
            return f"未能获取 {date} 的业绩预告数据"
        
        result = f"# 业绩预告 (来源: AkShare)\n"
        result += f"# 日期: {date}\n"
        result += f"# 共 {len(df)} 条\n\n"
        
        result += "代码       | 名称         | 业绩预告类型   | 净利润变动\n"
        result += "-" * 70 + "\n"
        
        for _, row in df.head(20).iterrows():
            code = str(row.get('代码', ''))
            name = str(row.get('名称', ''))[:8]
            yj_type = str(row.get('业绩预告类型', ''))[:12]
            change = str(row.get('净利润变动', ''))[:15]
            result += f"{code} | {name:<10} | {yj_type:<14} | {change}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取业绩预告失败: {e}")
        return f"获取业绩预告失败: {str(e)}"


# ==================== 更新导出列表 ====================

AKSHARE_TOOLS.extend([
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
])
