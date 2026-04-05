"""
数据 API Router
提供股票、指数、基金、财务、特色数据等 API
支持缓存
"""
import os
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
import pandas as pd
import json

from app.services.data import (
    get_stock_service,
    get_index_service,
    get_fund_service,
    get_financial_service,
    get_market_service,
    get_cache_service,
    generate_cache_key,
)

router = APIRouter(prefix="/api/data", tags=["数据接口"])


class StockQuoteResponse(BaseModel):
    code: str
    quote: Optional[dict] = None
    from_cache: bool = False


class StockDailyResponse(BaseModel):
    code: str
    data: Optional[list] = None
    count: int = 0
    from_cache: bool = False


class IndexListResponse(BaseModel):
    codes: dict


class FundSpotResponse(BaseModel):
    etf: Optional[list] = None
    lof: Optional[list] = None


class MoneyFlowResponse(BaseModel):
    code: str
    data: Optional[list] = None
    from_cache: bool = False


class MarginResponse(BaseModel):
    code: str
    data: Optional[list] = None
    from_cache: bool = False


class LeaderboardResponse(BaseModel):
    date: str
    data: Optional[list] = None
    from_cache: bool = False


@router.get("/status")
async def get_data_status():
    """获取数据服务状态"""
    from app.services.data.tushare_client import get_tushare_client
    from app.services.data.akshare_client import get_akshare_client
    from app.services.data.cache_service import get_cache_service
    from app.services.stock_data import get_stock_provider
    
    tushare = get_tushare_client()
    akshare = get_akshare_client()
    cache = get_cache_service()
    cache_status = cache.get_status()
    
    # Check Juhe provider
    juhe_available = False
    try:
        juhe = get_stock_provider("juhe")
        if juhe:
            juhe_available = juhe.is_available()
    except Exception:
        pass
    
    # Check BaoStock provider
    baostock_available = False
    try:
        baostock = get_stock_provider("baostock")
        if baostock:
            baostock_available = baostock.is_available()
    except Exception:
        pass
    
    return {
        "tushare_connected": tushare.is_connected,
        "akshare_available": akshare.is_available,
        "juhe_available": juhe_available,
        "baostock_available": baostock_available,
        "cache": cache_status,
    }


@router.get("/cache/status")
async def get_cache_status():
    """获取缓存状态"""
    cache = get_cache_service()
    return cache.get_status()


@router.post("/cache/clear")
async def clear_cache():
    """清空所有缓存"""
    cache = get_cache_service()
    cache.clear_all()
    return {"message": "缓存已清空"}


@router.post("/cache/clear/{stock_code}")
async def clear_stock_cache(stock_code: str):
    """清除指定股票的缓存"""
    cache = get_cache_service()
    data_types = ["quote", "daily", "indicator", "moneyflow", "margin"]
    
    for data_type in data_types:
        cache_key = generate_cache_key(data_type, stock_code)
        cache.delete(cache_key)
    
    return {"message": f"股票 {stock_code} 的缓存已清除"}


@router.get("/stock/quote/{stock_code}")
async def get_stock_quote(
    stock_code: str,
    use_cache: bool = Query(default=True, description="是否使用缓存"),
    force_refresh: bool = Query(default=False, description="强制刷新")
):
    """获取股票实时行情"""
    cache = get_cache_service()
    cache_key = generate_cache_key("quote", stock_code)
    
    # 尝试从缓存获取
    if use_cache and not force_refresh:
        cached_data = cache.get(cache_key)
        if cached_data:
            return StockQuoteResponse(
                code=stock_code, 
                quote=cached_data.get("data"),
                from_cache=True
            )
    
    # 获取新数据
    stock = get_stock_service()
    quote = stock.get_quote(stock_code)
    
    if quote is None:
        raise HTTPException(status_code=404, detail="未获取到行情数据")
    
    # 保存缓存
    if use_cache:
        cache.set(cache_key, {"data": quote}, "quote")
    
    return StockQuoteResponse(code=stock_code, quote=quote, from_cache=False)


@router.get("/stock/daily/{stock_code}")
async def get_stock_daily(
    stock_code: str,
    start_date: str = Query(default="", description="开始日期 YYYYMMDD"),
    end_date: str = Query(default="", description="结束日期 YYYYMMDD"),
    use_cache: bool = Query(default=True, description="是否使用缓存"),
):
    """获取股票日线数据"""
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y%m%d")
    
    # 生成缓存键（包含日期范围）
    cache_key = f"daily:{stock_code}:{start_date}:{end_date}"
    cache = get_cache_service()
    
    # 尝试从缓存获取
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            return StockDailyResponse(
                code=stock_code,
                data=cached_data.get("data"),
                count=len(cached_data.get("data", [])),
                from_cache=True
            )
    
    # 获取新数据
    stock = get_stock_service()
    df = stock.get_daily(stock_code, start_date, end_date)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    data = df.to_dict('records')
    
    # 保存缓存
    if use_cache:
        cache.set(cache_key, {"data": data}, "daily")
    
    return StockDailyResponse(code=stock_code, data=data, count=len(data), from_cache=False)


@router.get("/stock/batch")
async def get_stock_batch(codes: str = Query(..., description="股票代码逗号分隔")):
    """批量获取股票行情"""
    stock = get_stock_service()
    
    code_list = [c.strip() for c in codes.split(",")]
    df = stock.get_quotes_batch(code_list)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"codes": code_list, "data": df.to_dict('records'), "count": len(df)}


@router.get("/index/list")
async def get_index_list():
    """获取常用指数列表"""
    index = get_index_service()
    return IndexListResponse(codes=index.get_index_list())


@router.get("/index/quote/{index_code}")
async def get_index_quote(index_code: str):
    """获取指数实时行情"""
    index = get_index_service()
    quote = index.get_quote(index_code)
    
    if quote is None:
        raise HTTPException(status_code=404, detail="未获取到行情数据")
    
    return {"code": index_code, "quote": quote}


@router.get("/index/daily/{index_code}")
async def get_index_daily(index_code: str):
    """获取指数日线数据"""
    index = get_index_service()
    df = index.get_daily(index_code)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"code": index_code, "data": df.to_dict('records'), "count": len(df)}


@router.get("/index/realtime")
async def get_index_realtime():
    """获取所有指数实时行情"""
    index = get_index_service()
    df = index.get_realtime_all()
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"data": df.head(100).to_dict('records'), "count": len(df)}


@router.get("/fund/etf")
async def get_etf_spot(limit: int = Query(default=50, le=100)):
    """获取 ETF 实时行情"""
    fund = get_fund_service()
    df = fund.get_etf_spot()
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"data": df.head(limit).to_dict('records'), "count": len(df)}


@router.get("/fund/lof")
async def get_lof_spot(limit: int = Query(default=50, le=100)):
    """获取 LOF 实时行情"""
    fund = get_fund_service()
    df = fund.get_lof_spot()
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"data": df.head(limit).to_dict('records'), "count": len(df)}


@router.get("/financial/indicator/{stock_code}")
async def get_fina_indicator(
    stock_code: str, 
    limit: int = Query(default=4, le=12),
    use_cache: bool = Query(default=True, description="是否使用缓存")
):
    """获取财务指标"""
    cache = get_cache_service()
    cache_key = f"indicator:{stock_code}:{limit}"
    
    # 尝试从缓存获取
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            return {
                "code": stock_code,
                "data": cached_data.get("data"),
                "count": len(cached_data.get("data", [])),
                "from_cache": True
            }
    
    # 获取新数据
    financial = get_financial_service()
    df = financial.get_fina_indicator(stock_code, limit)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    data = df.to_dict('records')
    
    # 保存缓存
    if use_cache:
        cache.set(cache_key, {"data": data}, "indicator")
    
    return {"code": stock_code, "data": data, "count": len(data), "from_cache": False}


@router.get("/financial/income/{stock_code}")
async def get_income(stock_code: str, limit: int = Query(default=4, le=12)):
    """获取利润表"""
    financial = get_financial_service()
    df = financial.get_income(stock_code, limit)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"code": stock_code, "data": df.to_dict('records'), "count": len(df)}


@router.get("/financial/balance/{stock_code}")
async def get_balance_sheet(stock_code: str, limit: int = Query(default=4, le=12)):
    """获取资产负债表"""
    financial = get_financial_service()
    df = financial.get_balance_sheet(stock_code, limit)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"code": stock_code, "data": df.to_dict('records'), "count": len(df)}


@router.get("/financial/cashflow/{stock_code}")
async def get_cashflow(stock_code: str, limit: int = Query(default=4, le=12)):
    """获取现金流量表"""
    financial = get_financial_service()
    df = financial.get_cashflow(stock_code, limit)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"code": stock_code, "data": df.to_dict('records'), "count": len(df)}


@router.get("/financial/top10/{stock_code}")
async def get_top10_holders(stock_code: str):
    """获取前十大股东"""
    financial = get_financial_service()
    df = financial.get_top10_holders(stock_code)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"code": stock_code, "data": df.to_dict('records'), "count": len(df)}


@router.get("/financial/dividend/{stock_code}")
async def get_dividend(stock_code: str):
    """获取分红送配"""
    financial = get_financial_service()
    df = financial.get_dividend(stock_code)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"code": stock_code, "data": df.to_dict('records'), "count": len(df)}


@router.get("/market/moneyflow/{stock_code}")
async def get_moneyflow(
    stock_code: str, 
    days: int = Query(default=10, le=60),
    use_cache: bool = Query(default=True, description="是否使用缓存")
):
    """获取资金流向"""
    cache = get_cache_service()
    cache_key = f"moneyflow:{stock_code}:{days}"
    
    # 尝试从缓存获取
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            return MoneyFlowResponse(
                code=stock_code,
                data=cached_data.get("data"),
                from_cache=True
            )
    
    # 获取新数据
    market = get_market_service()
    df = market.get_moneyflow(stock_code, days)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    data = df.to_dict('records')
    
    # 保存缓存
    if use_cache:
        cache.set(cache_key, {"data": data}, "moneyflow")
    
    return MoneyFlowResponse(code=stock_code, data=data, from_cache=False)


@router.get("/market/margin/{stock_code}")
async def get_margin(
    stock_code: str, 
    days: int = Query(default=10, le=60),
    use_cache: bool = Query(default=True, description="是否使用缓存")
):
    """获取融资融券"""
    cache = get_cache_service()
    cache_key = f"margin:{stock_code}:{days}"
    
    # 尝试从缓存获取
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            return MarginResponse(
                code=stock_code,
                data=cached_data.get("data"),
                from_cache=True
            )
    
    # 获取新数据
    market = get_market_service()
    df = market.get_margin(stock_code, days)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    data = df.to_dict('records')
    
    # 保存缓存
    if use_cache:
        cache.set(cache_key, {"data": data}, "margin")
    
    return MarginResponse(code=stock_code, data=data, from_cache=False)


@router.get("/market/leaderboard")
async def get_leaderboard(
    date: str = Query(default="", description="日期 YYYYMMDD"),
    use_cache: bool = Query(default=True, description="是否使用缓存")
):
    """获取龙虎榜"""
    if not date:
        date = datetime.now().strftime("%Y%m%d")
    
    cache = get_cache_service()
    cache_key = f"leaderboard:{date}"
    
    # 尝试从缓存获取
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            return LeaderboardResponse(
                date=date,
                data=cached_data.get("data"),
                from_cache=True
            )
    
    # 获取新数据
    market = get_market_service()
    df = market.get_leaderboard(date)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    data = df.to_dict('records')
    
    # 保存缓存
    if use_cache:
        cache.set(cache_key, {"data": data}, "leaderboard")
    
    return LeaderboardResponse(date=date, data=data, from_cache=False)


@router.get("/market/hsgt")
async def get_moneyflow_hsgt():
    """获取北向资金流向"""
    market = get_market_service()
    df = market.get_moneyflow_hsgt()
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"data": df.to_dict('records'), "count": len(df)}


@router.get("/market/industry-flow")
async def get_industry_flow(limit: int = Query(default=10, le=50)):
    """获取行业资金流向"""
    market = get_market_service()
    df = market.get_industry_flow(limit)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"data": df.to_dict('records'), "count": len(df)}


@router.get("/market/concept-flow")
async def get_concept_flow(limit: int = Query(default=10, le=50)):
    """获取概念资金流向"""
    market = get_market_service()
    df = market.get_concept_flow(limit)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="未获取到数据")
    
    return {"data": df.to_dict('records'), "count": len(df)}


# ========================================
# 自动变量查询端点
# ========================================

# 预定义变量配置
VARIABLE_CONFIGS = {
    "quote": {"name": "q_{code}", "type": "quote", "desc": "实时行情"},
    "daily": {"name": "d_{code}", "type": "daily", "desc": "日线数据"},
    "indicator": {"name": "fi_{code}", "type": "indicator", "desc": "财务指标"},
    "moneyflow": {"name": "mf_{code}", "type": "moneyflow", "desc": "资金流向"},
    "margin": {"name": "mg_{code}", "type": "margin", "desc": "融资融券"},
}


@router.post("/query/{stock_code}")
async def query_stock_with_variables(
    stock_code: str,
    save_variables: bool = Query(default=True, description="是否自动保存变量")
):
    """
    查询股票数据并自动保存为预定义变量
    
    变量名格式：
    - q_{code}: 实时行情
    - d_{code}: 日线数据  
    - fi_{code}: 财务指标
    - mf_{code}: 资金流向
    - mg_{code}: 融资融券
    """
    from app.database import SessionLocal
    from app.models.context import ContextVariable
    
    db = SessionLocal()
    results = {}
    tushare_available = False
    
    # 检查 Tushare 是否可用
    from app.services.data.tushare_client import get_tushare_client
    tushare = get_tushare_client()
    tushare_available = tushare.is_connected
    
    try:
        stock = get_stock_service()
        market = get_market_service()
        
        # 1. 获取实时行情
        quote = stock.get_quote(stock_code)
        var_name = VARIABLE_CONFIGS["quote"]["name"].format(code=stock_code)
        if quote:
            results["quote"] = {"available": True, "data": quote}
            if save_variables:
                _upsert_variable(db, var_name, "quote", stock_code, quote, True, None, "实时行情")
        else:
            results["quote"] = {"available": False, "data": None, "reason": "未获取到数据"}
            if save_variables:
                _upsert_variable(db, var_name, "quote", stock_code, {}, False, "未获取到数据", "实时行情")
        
        # 2. 获取日线数据
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")
        daily_df = stock.get_daily(stock_code, start_date, end_date)
        var_name = VARIABLE_CONFIGS["daily"]["name"].format(code=stock_code)
        if daily_df is not None and not daily_df.empty:
            daily_data = daily_df.to_dict('records')
            results["daily"] = {"available": True, "data": daily_data}
            if save_variables:
                _upsert_variable(db, var_name, "daily", stock_code, daily_data, True, None, "日线数据")
        else:
            results["daily"] = {"available": False, "data": None, "reason": "未获取到数据"}
            if save_variables:
                _upsert_variable(db, var_name, "daily", stock_code, {}, False, "未获取到数据", "日线数据")
        
        # 3. 获取财务指标（需要 Tushare）
        var_name = VARIABLE_CONFIGS["indicator"]["name"].format(code=stock_code)
        if tushare_available:
            financial = get_financial_service()
            indicator_df = financial.get_fina_indicator(stock_code, 4)
            if indicator_df is not None and not indicator_df.empty:
                indicator_data = indicator_df.to_dict('records')
                results["indicator"] = {"available": True, "data": indicator_data}
                if save_variables:
                    _upsert_variable(db, var_name, "indicator", stock_code, indicator_data, True, None, "财务指标")
            else:
                results["indicator"] = {"available": False, "data": None, "reason": "未获取到数据"}
                if save_variables:
                    _upsert_variable(db, var_name, "indicator", stock_code, {}, False, "未获取到数据", "财务指标")
        else:
            results["indicator"] = {"available": False, "data": None, "reason": "Tushare Token 未配置"}
            if save_variables:
                _upsert_variable(db, var_name, "indicator", stock_code, {}, False, "Tushare Token 未配置", "财务指标")
        
        # 4. 获取资金流向（需要 Tushare）
        var_name = VARIABLE_CONFIGS["moneyflow"]["name"].format(code=stock_code)
        if tushare_available:
            moneyflow_df = market.get_moneyflow(stock_code, 10)
            if moneyflow_df is not None and not moneyflow_df.empty:
                moneyflow_data = moneyflow_df.to_dict('records')
                results["moneyflow"] = {"available": True, "data": moneyflow_data}
                if save_variables:
                    _upsert_variable(db, var_name, "moneyflow", stock_code, moneyflow_data, True, None, "资金流向")
            else:
                results["moneyflow"] = {"available": False, "data": None, "reason": "未获取到数据"}
                if save_variables:
                    _upsert_variable(db, var_name, "moneyflow", stock_code, {}, False, "未获取到数据", "资金流向")
        else:
            results["moneyflow"] = {"available": False, "data": None, "reason": "Tushare Token 未配置"}
            if save_variables:
                _upsert_variable(db, var_name, "moneyflow", stock_code, {}, False, "Tushare Token 未配置", "资金流向")
        
        # 5. 获取融资融券（需要 Tushare）
        var_name = VARIABLE_CONFIGS["margin"]["name"].format(code=stock_code)
        if tushare_available:
            margin_df = market.get_margin(stock_code, 10)
            if margin_df is not None and not margin_df.empty:
                margin_data = margin_df.to_dict('records')
                results["margin"] = {"available": True, "data": margin_data}
                if save_variables:
                    _upsert_variable(db, var_name, "margin", stock_code, margin_data, True, None, "融资融券")
            else:
                results["margin"] = {"available": False, "data": None, "reason": "未获取到数据"}
                if save_variables:
                    _upsert_variable(db, var_name, "margin", stock_code, {}, False, "未获取到数据", "融资融券")
        else:
            results["margin"] = {"available": False, "data": None, "reason": "Tushare Token 未配置"}
            if save_variables:
                _upsert_variable(db, var_name, "margin", stock_code, {}, False, "Tushare Token 未配置", "融资融券")
        
        return {
            "stock_code": stock_code,
            "results": results,
            "variables_saved": save_variables,
            "tushare_available": tushare_available
        }
    
    except Exception as e:
        return {"error": str(e), "stock_code": stock_code}
    finally:
        db.close()


def _upsert_variable(db, name, var_type, symbol, data, available, reason, description):
    """辅助函数：创建或更新变量"""
    from datetime import datetime
    
    existing = db.query(ContextVariable).filter(ContextVariable.name == name).first()
    
    if existing:
        existing.type = var_type
        existing.symbol = symbol
        existing.data = data
        existing.available = available
        existing.reason = reason
        existing.description = description
        existing.updated_at = datetime.now()
    else:
        new_var = ContextVariable(
            name=name,
            type=var_type,
            symbol=symbol,
            data=data,
            available=available,
            reason=reason,
            description=description
        )
        db.add(new_var)
    
    db.commit()
