"""
LangChain Tools - BaoStock 数据源工具
基于 BaoStock Python API 封装
"""
import logging
from typing import Annotated, Optional
from datetime import datetime, timedelta
import pandas as pd
from langchain_core.tools import tool

logger = logging.getLogger("baostock_tools")

BAOSTOCK_AVAILABLE = False
try:
    import baostock as bs
    BAOSTOCK_AVAILABLE = True
except ImportError:
    bs = None


def _ensure_login():
    """确保已登录 BaoStock"""
    if not BAOSTOCK_AVAILABLE:
        raise RuntimeError("BaoStock 库未安装")
    lg = bs.login()
    if lg.error_code != '0':
        raise RuntimeError(f"BaoStock 登录失败: {lg.error_msg}")
    return True


def _to_bs_code(stock_code: str) -> str:
    """转换为 BaoStock 代码格式"""
    code = str(stock_code).strip()
    if '.' in code:
        code = code.split('.')[0]
    if code.startswith('6'):
        return f"sh.{code}"
    elif code.startswith(('0', '3')):
        return f"sz.{code}"
    elif code.startswith('8'):
        return f"bj.{code}"
    return f"sz.{code}"


# ==================== 行情数据 ====================

@tool
def get_stock_daily_baostock(
    stock_code: Annotated[str, "股票代码，如 600519、000001"],
    days: Annotated[int, "获取天数，默认30天"] = 30
) -> str:
    """
    【BaoStock】获取股票日线数据
    
    返回：日期、开盘价、最高价、最低价、收盘价、成交量、成交额、换手率、涨跌幅
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        bs_code = _to_bs_code(stock_code)
        
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,code,open,high,low,close,preclose,volume,amount,turn,pctChg",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"
        )
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取股票 {stock_code} 的日线数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        result = f"# {stock_code} 日线数据 (来源: BaoStock)\n"
        result += f"# 日期范围: {df['date'].iloc[0]} ~ {df['date'].iloc[-1]}\n"
        result += f"# 共 {len(df)} 条记录\n\n"
        result += "日期       | 开盘    | 最高    | 最低    | 收盘    | 成交量   | 涨跌幅\n"
        result += "-" * 80 + "\n"
        
        for _, row in df.tail(10).iterrows():
            result += f"{row['date']} | {row['open']:>7} | {row['high']:>7} | {row['low']:>7} | {row['close']:>7} | {row['volume']:>8} | {row['pctChg']}%\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取日线数据失败: {e}")
        return f"获取日线数据失败: {str(e)}"


@tool
def get_stock_weekly_baostock(
    stock_code: Annotated[str, "股票代码，如 600519、000001"],
    weeks: Annotated[int, "获取周数，默认20周"] = 20
) -> str:
    """
    【BaoStock】获取股票周线数据
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
        bs_code = _to_bs_code(stock_code)
        
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,code,open,high,low,close,volume,amount,turn,pctChg",
            start_date=start_date,
            end_date=end_date,
            frequency="w",
            adjustflag="3"
        )
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取股票 {stock_code} 的周线数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        result = f"# {stock_code} 周线数据 (来源: BaoStock)\n"
        result += f"# 共 {len(df)} 周\n\n"
        
        for _, row in df.iterrows():
            result += f"{row['date']} | 开盘:{row['open']} 收盘:{row['close']} 涨跌幅:{row['pctChg']}%\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取周线数据失败: {e}")
        return f"获取周线数据失败: {str(e)}"


@tool
def get_stock_monthly_baostock(
    stock_code: Annotated[str, "股票代码，如 600519、000001"],
    months: Annotated[int, "获取月数，默认12月"] = 12
) -> str:
    """
    【BaoStock】获取股票月线数据
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d')
        bs_code = _to_bs_code(stock_code)
        
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,code,open,high,low,close,volume,amount,turn,pctChg",
            start_date=start_date,
            end_date=end_date,
            frequency="m",
            adjustflag="3"
        )
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取股票 {stock_code} 的月线数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        result = f"# {stock_code} 月线数据 (来源: BaoStock)\n"
        result += f"# 共 {len(df)} 月\n\n"
        
        for _, row in df.iterrows():
            result += f"{row['date']} | 开盘:{row['open']} 收盘:{row['close']} 涨跌幅:{row['pctChg']}%\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取月线数据失败: {e}")
        return f"获取月线数据失败: {str(e)}"


# ==================== 估值数据 ====================

@tool
def get_stock_valuation_baostock(
    stock_code: Annotated[str, "股票代码，如 600519、000001"],
    days: Annotated[int, "获取天数，默认30天"] = 30
) -> str:
    """
    【BaoStock】获取股票估值数据
    
    返回：PE(TTM)、PB、PS(TTM)、PCF(TTM) 等估值指标，以及是否ST股票
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        bs_code = _to_bs_code(stock_code)
        
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM,turn,tradestatus,isST",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"
        )
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取股票 {stock_code} 的估值数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        latest = df.iloc[-1]
        
        result = f"# {stock_code} 估值数据 (来源: BaoStock)\n"
        result += f"# 更新日期: {latest['date']}\n\n"
        result += f"## 基本行情\n"
        result += f"- 当前价格: {latest['close']} 元\n"
        result += f"- 换手率: {latest['turn']}%\n"
        result += f"- 交易状态: {'正常' if latest['tradestatus'] == '1' else '停牌'}\n"
        result += f"- ST标记: {'是' if latest['isST'] == '1' else '否'}\n\n"
        result += f"## 估值指标\n"
        
        pe = latest.get('peTTM', 'N/A')
        pb = latest.get('pbMRQ', 'N/A')
        ps = latest.get('psTTM', 'N/A')
        pcf = latest.get('pcfNcfTTM', 'N/A')
        
        result += f"- PE(TTM): {pe}\n"
        result += f"- PB(MRQ): {pb}\n"
        result += f"- PS(TTM): {ps}\n"
        result += f"- PCF(TTM): {pcf}\n"
        
        if pe != 'N/A' and pe:
            try:
                pe_val = float(pe)
                if pe_val < 0:
                    result += "\n*注: PE为负表示亏损*\n"
                elif pe_val < 20:
                    result += "\n*注: PE较低，估值相对合理*\n"
                elif pe_val > 50:
                    result += "\n*注: PE较高，估值偏高*\n"
            except:
                pass
        
        return result
        
    except Exception as e:
        logger.error(f"获取估值数据失败: {e}")
        return f"获取估值数据失败: {str(e)}"


# ==================== 财务数据 ====================

@tool
def get_stock_profit_baostock(
    stock_code: Annotated[str, "股票代码，如 600519、000001"],
    year: Annotated[int, "年份，默认2024"] = 2024,
    quarter: Annotated[int, "季度，1-4，默认4"] = 4
) -> str:
    """
    【BaoStock】获取股票盈利能力数据（利润表）
    
    返回：营业收入、净利润、ROE等盈利指标
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        bs_code = _to_bs_code(stock_code)
        rs = bs.query_profit_data(code=bs_code, year=year, quarter=quarter)
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取股票 {stock_code} {year}年第{quarter}季度盈利数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        row = df.iloc[0]
        
        result = f"# {stock_code} 盈利能力数据 (来源: BaoStock)\n"
        result += f"# 报告期: {year}年第{quarter}季度\n\n"
        
        def fmt(val):
            if val is None or val == '':
                return 'N/A'
            try:
                return f"{float(val):,.2f}"
            except:
                return str(val)
        
        result += f"## 利润表关键指标\n"
        result += f"- 营业总收入: {fmt(row.get('revenue'))} 元\n"
        result += f"- 营业收入: {fmt(row.get('operRevenue'))} 元\n"
        result += f"- 净利润: {fmt(row.get('netProfit'))} 元\n"
        result += f"- 归属净利润: {fmt(row.get('nIncome'))} 元\n\n"
        
        result += f"## 盈利能力指标\n"
        result += f"- ROE(净资产收益率): {fmt(row.get('roe'))}%\n"
        result += f"- 毛利率: {fmt(row.get('grossProfitMargin'))}%\n"
        result += f"- 净利率: {fmt(row.get('netProfitMargin'))}%\n"
        result += f"- ROA(总资产收益率): {fmt(row.get('roa'))}%\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取盈利数据失败: {e}")
        return f"获取盈利数据失败: {str(e)}"


@tool
def get_stock_balance_baostock(
    stock_code: Annotated[str, "股票代码，如 600519、000001"],
    year: Annotated[int, "年份，默认2024"] = 2024,
    quarter: Annotated[int, "季度，1-4，默认4"] = 4
) -> str:
    """
    【BaoStock】获取股票资产负债表数据
    
    返回：总资产、总负债、资产负债率等
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        bs_code = _to_bs_code(stock_code)
        rs = bs.query_balance_data(code=bs_code, year=year, quarter=quarter)
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取股票 {stock_code} {year}年第{quarter}季度资产负债表数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        row = df.iloc[0]
        
        def fmt(val):
            if val is None or val == '':
                return 'N/A'
            try:
                return f"{float(val):,.2f}"
            except:
                return str(val)
        
        result = f"# {stock_code} 资产负债表 (来源: BaoStock)\n"
        result += f"# 报告期: {year}年第{quarter}季度\n\n"
        
        result += f"## 资产\n"
        result += f"- 总资产: {fmt(row.get('totalAssets'))} 元\n"
        result += f"- 流动资产: {fmt(row.get('totalCurAssets'))} 元\n"
        result += f"- 非流动资产: {fmt(row.get('totalNonCurAssets'))} 元\n\n"
        
        result += f"## 负债\n"
        result += f"- 总负债: {fmt(row.get('totalLiab'))} 元\n"
        result += f"- 流动负债: {fmt(row.get('totalCurLiab'))} 元\n"
        result += f"- 非流动负债: {fmt(row.get('totalNonCurLiab'))} 元\n\n"
        
        result += f"## 股东权益\n"
        result += f"- 股东权益: {fmt(row.get('totalHldrEqy'))} 元\n"
        result += f"- 资产负债率: {fmt(row.get('liabAssetsRatio'))}%\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取资产负债表数据失败: {e}")
        return f"获取资产负债表数据失败: {str(e)}"


@tool
def get_stock_cashflow_baostock(
    stock_code: Annotated[str, "股票代码，如 600519、000001"],
    year: Annotated[int, "年份，默认2024"] = 2024,
    quarter: Annotated[int, "季度，1-4，默认4"] = 4
) -> str:
    """
    【BaoStock】获取股票现金流量表数据
    
    返回：经营现金流、投资现金流、筹资现金流等
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        bs_code = _to_bs_code(stock_code)
        rs = bs.query_cash_flow_data(code=bs_code, year=year, quarter=quarter)
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取股票 {stock_code} {year}年第{quarter}季度现金流数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        row = df.iloc[0]
        
        def fmt(val):
            if val is None or val == '':
                return 'N/A'
            try:
                return f"{float(val):,.2f}"
            except:
                return str(val)
        
        result = f"# {stock_code} 现金流量表 (来源: BaoStock)\n"
        result += f"# 报告期: {year}年第{quarter}季度\n\n"
        
        result += f"## 现金流\n"
        result += f"- 经营活动现金流: {fmt(row.get('netCashFlowsOperAct'))} 元\n"
        result += f"- 投资活动现金流: {fmt(row.get('netCashFlowsInvAct'))} 元\n"
        result += f"- 筹资活动现金流: {fmt(row.get('netCashFlowsFinAct'))} 元\n"
        result += f"- 现金流净增加额: {fmt(row.get('netCashFlows'))} 元\n"
        result += f"- 期末现金余额: {fmt(row.get('cashAndEquivalentsEndPeriod'))} 元\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取现金流量表数据失败: {e}")
        return f"获取现金流量表数据失败: {str(e)}"


# ==================== 指数成分股 ====================

@tool
def get_hs300_constituents_baostock(
    date: Annotated[str, "查询日期，格式YYYY-MM-DD，默认最新"] = ""
) -> str:
    """
    【BaoStock】获取沪深300指数成分股
    
    返回：成分股代码、名称、纳入日期等
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        rs = bs.query_hs300_stocks(date)
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取沪深300成分股数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        result = f"# 沪深300成分股 (来源: BaoStock)\n"
        result += f"# 查询日期: {date}\n"
        result += f"# 共 {len(df)} 只股票\n\n"
        
        result += "代码       | 名称\n"
        result += "-" * 40 + "\n"
        
        for _, row in df.iterrows():
            result += f"{row['code']} | {row['code_name']}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取沪深300成分股失败: {e}")
        return f"获取沪深300成分股失败: {str(e)}"


@tool
def get_sz50_constituents_baostock() -> str:
    """
    【BaoStock】获取上证50指数成分股
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        rs = bs.query_sz50_stocks()
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取上证50成分股数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        result = f"# 上证50成分股 (来源: BaoStock)\n"
        result += f"# 共 {len(df)} 只股票\n\n"
        
        result += "代码       | 名称\n"
        result += "-" * 40 + "\n"
        
        for _, row in df.iterrows():
            result += f"{row['code']} | {row['code_name']}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取上证50成分股失败: {e}")
        return f"获取上证50成分股失败: {str(e)}"


@tool
def get_zz500_constituents_baostock() -> str:
    """
    【BaoStock】获取中证500指数成分股
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        rs = bs.query_zz500_stocks()
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取中证500成分股数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        result = f"# 中证500成分股 (来源: BaoStock)\n"
        result += f"# 共 {len(df)} 只股票\n\n"
        
        result += "代码       | 名称\n"
        result += "-" * 40 + "\n"
        
        for _, row in df.head(50).iterrows():
            result += f"{row['code']} | {row['code_name']}\n"
        
        if len(df) > 50:
            result += f"\n... 还有 {len(df) - 50} 只股票\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取中证500成分股失败: {e}")
        return f"获取中证500成分股失败: {str(e)}"


# ==================== 行业分类 ====================

@tool
def get_stock_industry_baostock(
    stock_code: Annotated[str, "股票代码，如 600519、000001"]
) -> str:
    """
    【BaoStock】获取股票行业分类
    
    返回：所属行业、行业分类（证监会/申万）
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        bs_code = _to_bs_code(stock_code)
        rs = bs.query_stock_industry(code=bs_code)
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取股票 {stock_code} 的行业分类数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        row = df.iloc[0]
        
        result = f"# {stock_code} 行业分类 (来源: BaoStock)\n\n"
        result += f"- 股票代码: {row['code']}\n"
        result += f"- 股票名称: {row['code_name']}\n"
        result += f"- 所属行业(证监会): {row['industry']}\n"
        result += f"- 行业分类(申万): {row['industryClassification']}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取行业分类失败: {e}")
        return f"获取行业分类失败: {str(e)}"


@tool
def get_trade_calendar_baostock(
    start_date: Annotated[str, "开始日期，格式YYYY-MM-DD"] = "",
    end_date: Annotated[str, "结束日期，格式YYYY-MM-DD"] = ""
) -> str:
    """
    【BaoStock】获取交易日历
    
    返回指定日期范围内的交易日列表
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取交易日历数据"
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        try:
            trading_col = None
            for col in ["is_trading_day", "isTradedDay"]:
                if col in df.columns:
                    trading_col = col
                    break
            if trading_col:
                df = df[df[trading_col] == "1"]
        except Exception as e:
            logger.warning(f"过滤交易日失败: {e}")
        
        result = f"# 交易日历 (来源: BaoStock)\n"
        result += f"# 日期范围: {start_date} ~ {end_date}\n"
        result += f"# 共 {len(df)} 个交易日\n\n"
        
        try:
            date_col = 'calendar_date' if 'calendar_date' in df.columns else 'cal_date'
            
            for _, row in df.iterrows():
                result += f"{row[date_col]}\n"
        except Exception as e2:
            result += f"数据格式错误: {str(e2)}\n"
            result += f"列名: {list(df.columns)}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取交易日历失败: {e}")
        return f"获取交易日历失败: {str(e)}"


# ==================== 股票基本信息 ====================

@tool
def get_stock_info_baostock(stock_code: Annotated[str, "股票代码，如 600519、000001"]) -> str:
    """
    【BaoStock】获取股票基本信息
    
    返回：股票代码、名称、市场等基本信息
    """
    if not BAOSTOCK_AVAILABLE:
        return "BaoStock 库未安装"
    
    try:
        _ensure_login()
        
        bs_code = _to_bs_code(stock_code)
        rs = bs.query_stock_basic(code=bs_code)
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return f"未能获取股票 {stock_code} 的基本信息"
        
        row = data_list[0]
        
        code = row[0]
        name = row[1]
        
        market = "未知"
        if code.startswith('sh.6'):
            market = "上海证券交易所"
        elif code.startswith('sz.0') or code.startswith('sz.3'):
            market = "深圳证券交易所"
        elif code.startswith('bj.'):
            market = "北京证券交易所"
        
        result = f"# {stock_code} 基本信息 (来源: BaoStock)\n\n"
        result += f"- 股票代码: {code}\n"
        result += f"- 股票名称: {name}\n"
        result += f"- 上市日期: {row[2]}\n"
        result += f"- 所属市场: {market}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        return f"获取股票信息失败: {str(e)}"


# ==================== 导出所有工具 ====================

BAOSTOCK_TOOLS = [
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
