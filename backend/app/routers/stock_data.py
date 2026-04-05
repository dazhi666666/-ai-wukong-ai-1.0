"""
股票数据 API 路由
"""
import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from app.services.logging_manager import get_logger

logger = get_logger("stock_data.router")

try:
    from app.services.stock_data.factory import get_stock_provider, StockDataFactory
    from app.services.cache.cache_service import get_cache_service
    FACTORY_AVAILABLE = True
except Exception as e:
    logger.error(f"Failed to import stock_data modules: {e}")
    FACTORY_AVAILABLE = False
    get_stock_provider = None
    StockDataFactory = None
    get_cache_service = None

router = APIRouter(prefix="/api/stock", tags=["stock"])


class StockQuoteResponse(BaseModel):
    symbol: str
    data: dict


class StockHistoryResponse(BaseModel):
    symbol: str
    data: list


class StockConfigRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    is_enabled: bool = True


@router.get("/providers")
async def get_providers():
    """获取所有可用的数据源提供商"""
    if not FACTORY_AVAILABLE:
        raise HTTPException(status_code=500, detail="Stock data service not available")
    providers = StockDataFactory.get_all_providers()
    return {
        "providers": providers,
        "message": "Available stock data providers"
    }


@router.get("/quote")
async def get_stock_quote(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("tushare", description="数据源")
):
    """获取实时行情"""
    if not FACTORY_AVAILABLE:
        raise HTTPException(status_code=500, detail="Stock data service not available")
    
    cache = get_cache_service()
    cache_key = f"stock:quotes:{provider}:{symbol}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    quotes = await stock_provider.get_quotes(symbol)
    
    if quotes:
        cache.set(cache_key, quotes, ttl=60)
        return {"data": quotes, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No quote data for {symbol}")


@router.get("/history")
async def get_stock_history(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("tushare", description="数据源"),
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    period: str = Query("daily", description="周期: daily/weekly/monthly")
):
    """获取历史数据"""
    cache = get_cache_service()
    cache_key = f"stock:history:{provider}:{symbol}:{start_date}:{end_date}:{period}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    history = await stock_provider.get_historical(symbol, start_date, end_date, period)
    
    if history is not None:
        import pandas as pd
        if hasattr(history, 'to_dict'):
            data = history.to_dict(orient='records')
        elif isinstance(history, pd.DataFrame):
            data = history.to_dict(orient='records')
        else:
            data = history
        
        cache.set(cache_key, data, ttl=1800)
        return {"data": data, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No historical data for {symbol}")


@router.get("/financial")
async def get_stock_financial(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("tushare", description="数据源"),
    limit: int = Query(4, description="返回记录数")
):
    """获取财务数据"""
    cache = get_cache_service()
    cache_key = f"stock:financial:{provider}:{symbol}:{limit}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    financial = await stock_provider.get_financial(symbol, limit)
    
    if financial:
        cache.set(cache_key, financial, ttl=86400)
        return {"data": financial, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No financial data for {symbol}")


@router.get("/info")
async def get_stock_info(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("baostock", description="数据源")
):
    """获取股票详细信息"""
    cache = get_cache_service()
    cache_key = f"stock:info:{provider}:{symbol}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    if not hasattr(stock_provider, 'get_stock_basic_info'):
        raise HTTPException(status_code=400, detail=f"Provider {provider} does not support get_stock_basic_info")
    
    info = await stock_provider.get_stock_basic_info(symbol)
    
    if info:
        cache.set(cache_key, info, ttl=86400)
        return {"data": info, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No info data for {symbol}")


@router.get("/valuation")
async def get_stock_valuation(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("baostock", description="数据源"),
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD")
):
    """获取估值数据（PE、PB等）"""
    cache = get_cache_service()
    cache_key = f"stock:valuation:{provider}:{symbol}:{trade_date}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    if not hasattr(stock_provider, 'get_valuation_data'):
        raise HTTPException(status_code=400, detail=f"Provider {provider} does not support get_valuation_data")
    
    valuation = await stock_provider.get_valuation_data(symbol, trade_date)
    
    if valuation:
        cache.set(cache_key, valuation, ttl=86400)
        return {"data": valuation, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No valuation data for {symbol}")


@router.get("/list")
async def get_stock_list(
    provider: str = Query("tushare", description="数据源"),
    market: Optional[str] = Query(None, description="市场: CN/HK/US"),
    limit: int = Query(100, description="返回数量限制")
):
    """获取股票列表"""
    cache = get_cache_service()
    cache_key = f"stock:list:{provider}:{market}:{limit}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    stock_list = await stock_provider.get_stock_list(market)
    
    if stock_list:
        limited_list = stock_list[:limit]
        cache.set(cache_key, limited_list, ttl=86400)
        return {"data": limited_list, "cached": False, "total": len(stock_list)}
    
    return {"data": [], "cached": False, "total": 0}


@router.post("/test")
async def test_provider(
    provider: str = Query(..., description="数据源"),
    api_key: Optional[str] = Query(None, description="API Key")
):
    """测试数据源连接"""
    config = {}
    if api_key:
        config["api_key"] = api_key
    
    stock_provider = get_stock_provider(provider, config, force_new=True)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not found")
    
    connected = await stock_provider.connect()
    
    return {
        "provider": provider,
        "connected": connected,
        "message": "Connection successful" if connected else "Connection failed"
    }


@router.post("/config")
async def save_provider_config(
    provider: str = Query(..., description="数据源"),
    api_key: str = Query(..., description="API Key")
):
    """保存数据源配置"""
    import os
    import json
    from pathlib import Path
    
    config_file = Path(__file__).parent.parent / 'stock_config.json'
    
    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
        else:
            configs = {}
        
        configs[provider] = {"api_key": api_key}
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": f"{provider} 配置已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/daily")
async def get_stock_daily(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("baostock", description="数据源"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD")
):
    """获取日线数据"""
    from datetime import datetime, timedelta
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    cache = get_cache_service()
    cache_key = f"stock:daily:{provider}:{symbol}:{start_date}:{end_date}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    history = await stock_provider.get_historical(symbol, start_date, end_date, "daily")
    
    if history is not None:
        import pandas as pd
        if hasattr(history, 'to_dict'):
            data = history.to_dict(orient='records')
        elif isinstance(history, pd.DataFrame):
            data = history.to_dict(orient='records')
        else:
            data = history
        
        cache.set(cache_key, data, ttl=1800)
        return {"data": data, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No daily data for {symbol}")


@router.get("/indicator")
async def get_stock_indicator(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("tushare", description="数据源")
):
    """获取财务指标"""
    cache = get_cache_service()
    cache_key = f"stock:indicator:{provider}:{symbol}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    if not hasattr(stock_provider, 'get_financial'):
        raise HTTPException(status_code=400, detail=f"Provider {provider} does not support financial data")
    
    financial = await stock_provider.get_financial(symbol)
    
    if financial:
        cache.set(cache_key, financial, ttl=86400)
        return {"data": financial, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No financial data for {symbol}")


@router.get("/moneyflow")
async def get_stock_moneyflow(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("tushare", description="数据源"),
    days: int = Query(10, description="天数")
):
    """获取资金流向"""
    cache = get_cache_service()
    cache_key = f"stock:moneyflow:{provider}:{symbol}:{days}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    if not hasattr(stock_provider, 'get_moneyflow'):
        raise HTTPException(status_code=400, detail=f"Provider {provider} does not support moneyflow data")
    
    moneyflow = await stock_provider.get_moneyflow(symbol, days)
    
    if moneyflow:
        cache.set(cache_key, moneyflow, ttl=86400)
        return {"data": moneyflow, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No moneyflow data for {symbol}")


@router.get("/margin")
async def get_stock_margin(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("tushare", description="数据源"),
    days: int = Query(10, description="天数")
):
    """获取融资融券数据"""
    cache = get_cache_service()
    cache_key = f"stock:margin:{provider}:{symbol}:{days}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    if hasattr(stock_provider, 'get_margin'):
        margin = await stock_provider.get_margin(symbol, days)
    else:
        from app.services.data import get_market_service
        market = get_market_service()
        stock_code = symbol.replace("sh", "").replace("sz", "")
        if not stock_code.startswith("6") and not stock_code.startswith("0") and not stock_code.startswith("3"):
            stock_code = "0" + stock_code
        ts_code = stock_code + ".SZ" if symbol.startswith("sz") or (len(stock_code) == 6 and (stock_code.startswith("0") or stock_code.startswith("3"))) else stock_code + ".SH"
        margin = market.get_margin(ts_code, days)
    
    if margin:
        cache.set(cache_key, margin, ttl=86400)
        return {"data": margin, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No margin data for {symbol}")


@router.get("/index")
async def get_index_quote(
    index_type: int = Query(0, description="指数类型: 0=上证综合指数, 1=深证成指"),
    provider: str = Query("juhe", description="数据源")
):
    """获取指数行情"""
    if provider.lower() != "juhe":
        raise HTTPException(status_code=400, detail="Only juhe provider supports index data")
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    index_data = await stock_provider.get_index_quote(index_type)
    
    if index_data:
        return {"data": index_data, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No index data for type {index_type}")


@router.get("/formatted")
async def get_formatted_stock_data(
    symbol: str = Query(None, description="股票代码"),
    provider: str = Query("juhe", description="数据源 (支持: juhe/tushare/akshare)"),
    data_type: str = Query("quote", description="数据类型: quote/daily/financial/moneyflow/margin/leaderboard/etf/hsgt/industry/index"),
    include_order_book: bool = Query(True, description="是否包含五档盘口数据"),
    days: int = Query(30, description="历史数据天数"),
    date: str = Query(None, description="日期，格式 YYYYMMDD，用于龙虎榜等"),
    index_type: int = Query(0, description="指数类型: 0=上证, 1=深证"),
    limit: int = Query(20, description="返回数量限制")
):
    """
    获取格式化的股票数据 (用于 AI Prompt)
    
    支持的数据类型:
    - quote: 实时行情
    - daily: 历史日线
    - financial: 财务指标
    - moneyflow: 资金流向
    - margin: 融资融券
    - leaderboard: 龙虎榜
    - etf: ETF行情
    - hsgt: 北向资金
    - industry: 行业资金流
    - index: 指数行情
    """
    from datetime import datetime, timedelta
    
    if not FACTORY_AVAILABLE:
        raise HTTPException(status_code=500, detail="Stock data service not available")
    
    cache = get_cache_service()
    cache_key = f"stock:formatted:{provider}:{symbol or 'none'}:{data_type}:{days}:{date or 'none'}:{index_type}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return {"data": cached_data, "cached": True, "data_type": data_type}
    
    stock_provider = get_stock_provider(provider)
    if not stock_provider:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    if not stock_provider.connected:
        connected = await stock_provider.connect()
        if not connected:
            raise HTTPException(status_code=500, detail=f"Failed to connect to {provider}")
    
    formatted = ""
    raw_data = None
    
    try:
        from app.services.stock_data.providers.juhe import format_stock_data_for_prompt
        from app.services.stock_data import format_stock_data
        
        if data_type == "quote":
            if not symbol:
                raise HTTPException(status_code=400, detail="股票代码不能为空")
            raw_data = await stock_provider.get_quotes(symbol)
            if not raw_data:
                raise HTTPException(status_code=404, detail=f"无法获取 {symbol} 的行情数据")
            formatted = format_stock_data_for_prompt(raw_data, include_order_book=include_order_book)
            
        elif data_type == "daily":
            if not symbol:
                raise HTTPException(status_code=400, detail="股票代码不能为空")
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            raw_data = await stock_provider.get_historical(symbol, start_date, end_date, "daily")
            if raw_data is None:
                raise HTTPException(status_code=404, detail=f"无法获取 {symbol} 的历史数据")
            formatted = format_stock_data("daily", raw_data, limit=days)
            
        elif data_type == "financial":
            if not symbol:
                raise HTTPException(status_code=400, detail="股票代码不能为空")
            raw_data = await stock_provider.get_financial(symbol)
            if not raw_data:
                raise HTTPException(status_code=404, detail=f"无法获取 {symbol} 的财务数据")
            formatted = format_stock_data("financial", raw_data)
            
        elif data_type == "moneyflow":
            if not symbol:
                raise HTTPException(status_code=400, detail="股票代码不能为空")
            raw_data = await stock_provider.get_moneyflow(symbol, days)
            if not raw_data:
                raise HTTPException(status_code=404, detail=f"无法获取 {symbol} 的资金流向")
            formatted = format_stock_data("moneyflow", raw_data)
            
        elif data_type == "margin":
            if not symbol:
                raise HTTPException(status_code=400, detail="股票代码不能为空")
            if hasattr(stock_provider, 'get_margin'):
                raw_data = await stock_provider.get_margin(symbol, days)
            else:
                from app.services.data import get_market_service
                market = get_market_service()
                stock_code = symbol.replace("sh", "").replace("sz", "")
                if not stock_code.startswith("6") and not stock_code.startswith("0") and not stock_code.startswith("3"):
                    stock_code = "0" + stock_code
                ts_code = stock_code + ".SZ" if symbol.startswith("sz") or (len(stock_code) == 6 and stock_code.startswith("0") or stock_code.startswith("3")) else stock_code + ".SH"
                raw_data = market.get_margin(ts_code, days)
            if not raw_data:
                raise HTTPException(status_code=404, detail=f"无法获取 {symbol} 的融资融券数据")
            formatted = format_stock_data("margin", raw_data)
            
        elif data_type == "leaderboard":
            query_date = date or datetime.now().strftime("%Y%m%d")
            if hasattr(stock_provider, 'get_leaderboard'):
                raw_data = await stock_provider.get_leaderboard(query_date)
            else:
                from app.services.data import get_market_service
                market = get_market_service()
                raw_data = market.get_leaderboard(query_date)
            if not raw_data or (hasattr(raw_data, 'empty') and raw_data.empty):
                raise HTTPException(status_code=404, detail=f"无法获取 {query_date} 的龙虎榜数据")
            formatted = format_stock_data("leaderboard", raw_data)
            
        elif data_type == "etf":
            if hasattr(stock_provider, 'get_etf_spot'):
                raw_data = await stock_provider.get_etf_spot(limit)
            else:
                from app.services.data import get_fund_service
                fund = get_fund_service()
                raw_data = fund.get_etf_spot()
            if not raw_data or (hasattr(raw_data, 'empty') and raw_data.empty):
                raise HTTPException(status_code=404, detail="无法获取 ETF 行情数据")
            formatted = format_stock_data("etf", raw_data, limit=limit)
            
        elif data_type == "hsgt":
            if hasattr(stock_provider, 'get_hsgt_moneyflow'):
                raw_data = await stock_provider.get_hsgt_moneyflow()
            else:
                from app.services.data import get_market_service
                market = get_market_service()
                raw_data = market.get_moneyflow_hsgt()
            if not raw_data or (hasattr(raw_data, 'empty') and raw_data.empty):
                raise HTTPException(status_code=404, detail="无法获取北向资金数据")
            formatted = format_stock_data("hsgt", raw_data)
            
        elif data_type == "industry":
            if hasattr(stock_provider, 'get_industry_flow'):
                raw_data = await stock_provider.get_industry_flow(limit)
            else:
                from app.services.data import get_market_service
                market = get_market_service()
                raw_data = market.get_industry_flow(limit)
            if not raw_data or (hasattr(raw_data, 'empty') and raw_data.empty):
                raise HTTPException(status_code=404, detail="无法获取行业资金流数据")
            formatted = format_stock_data("industry", raw_data)
            
        elif data_type == "index":
            if hasattr(stock_provider, 'get_index_quote'):
                raw_data = await stock_provider.get_index_quote(index_type)
            else:
                from app.services.data import get_index_service
                index = get_index_service()
                code = "000001" if index_type == 0 else "399001"
                raw_data = index.get_quote(code)
            if not raw_data:
                raise HTTPException(status_code=404, detail=f"无法获取指数行情数据")
            formatted = format_stock_data("index", raw_data)
            
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据类型: {data_type}")
        
        if not formatted:
            formatted = "无数据"
        
        cache.set(cache_key, formatted, ttl=60)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"格式化数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"格式化失败: {str(e)}")
    
    return {"data": formatted, "cached": False, "data_type": data_type}
