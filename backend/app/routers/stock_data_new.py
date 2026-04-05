"""
股票数据 API Router
固定变量名，不同股票用 symbol 字段区分
"""
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.stock_data import Quote, Daily, Indicator, Moneyflow, Margin
from app.services.data import get_stock_service, get_financial_service, get_market_service

router = APIRouter(prefix="/api/stock", tags=["股票数据"])


@router.post("/init-tables")
async def init_tables():
    """初始化数据表"""
    from app.database import engine
    from app.models.stock_data import Quote, Daily, Indicator, Moneyflow, Margin
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # 检查并创建缺失的表
    for model in [Quote, Daily, Indicator, Moneyflow, Margin]:
        table_name = model.__tablename__
        if table_name not in existing_tables:
            model.__table__.create(engine)
    
    return {"message": "Tables initialized", "existing": existing_tables}


class StockDataResponse(BaseModel):
    symbol: str
    data: dict | list
    available: bool
    reason: Optional[str] = None
    updated_at: Optional[datetime] = None


class StockQueryResponse(BaseModel):
    quote: Optional[dict] = None
    daily: Optional[dict] = None
    indicator: Optional[dict] = None
    moneyflow: Optional[dict] = None
    margin: Optional[dict] = None


# ===== Quote 实时行情 =====

@router.get("/quote/{symbol}", response_model=StockDataResponse)
async def get_quote(symbol: str, db: Session = Depends(get_db)):
    """获取实时行情"""
    quote = db.query(Quote).filter(Quote.symbol == symbol).first()
    if not quote:
        return StockDataResponse(
            symbol=symbol,
            data={},
            available=False,
            reason="暂无数据"
        )
    return StockDataResponse(
        symbol=quote.symbol,
        data=quote.data,
        available=quote.available,
        reason=quote.reason,
        updated_at=quote.updated_at
    )


@router.post("/quote/{symbol}")
async def save_quote(symbol: str, db: Session = Depends(get_db)):
    """保存实时行情"""
    stock = get_stock_service()
    data = stock.get_quote(symbol)
    
    if data:
        quote = db.query(Quote).filter(Quote.symbol == symbol).first()
        if quote:
            quote.data = data
            quote.available = True
            quote.reason = None
        else:
            quote = Quote(symbol=symbol, data=data, available=True)
            db.add(quote)
        db.commit()
        return {"success": True, "available": True}
    else:
        quote = db.query(Quote).filter(Quote.symbol == symbol).first()
        if quote:
            quote.available = False
            quote.reason = "未获取到数据"
            db.commit()
        return {"success": True, "available": False, "reason": "未获取到数据"}


# ===== Daily 日线数据 =====

@router.get("/daily/{symbol}")
async def get_daily(symbol: str, db: Session = Depends(get_db)):
    """获取日线数据"""
    try:
        daily = db.query(Daily).filter(Daily.symbol == symbol).first()
        if not daily:
            return {
                "symbol": symbol,
                "data": [],
                "available": False,
                "reason": "暂无数据"
            }
        return {
            "symbol": daily.symbol,
            "data": daily.data,
            "available": daily.available,
            "reason": daily.reason,
            "updated_at": str(daily.updated_at) if daily.updated_at else None
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}


@router.post("/daily/{symbol}")
async def save_daily(symbol: str, start_date: str = "", end_date: str = "", db: Session = Depends(get_db)):
    """保存日线数据"""
    try:
        if not start_date:
            from datetime import datetime, timedelta
            start = datetime.now() - timedelta(days=365)
            start_date = start.strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        
        stock = get_stock_service()
        df = stock.get_daily(symbol, start_date, end_date)
        
        if df is not None and not df.empty:
            from datetime import date
            data = []
            for record in df.to_dict('records'):
                processed = {}
                for key, value in record.items():
                    if isinstance(value, (date,)):
                        processed[key] = value.strftime("%Y-%m-%d")
                    else:
                        processed[key] = value
                data.append(processed)
            
            daily = db.query(Daily).filter(Daily.symbol == symbol).first()
            if daily:
                daily.data = data
                daily.available = True
                daily.reason = None
            else:
                daily = Daily(symbol=symbol, data=data, available=True)
                db.add(daily)
            db.commit()
            return {"success": True, "available": True, "count": len(data)}
        else:
            daily = db.query(Daily).filter(Daily.symbol == symbol).first()
            if daily:
                daily.available = False
                daily.reason = "未获取到数据"
                db.commit()
            return {"success": True, "available": False, "reason": "未获取到数据"}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}


# ===== Indicator 财务指标 =====

@router.get("/indicator/{symbol}", response_model=StockDataResponse)
async def get_indicator(symbol: str, db: Session = Depends(get_db)):
    """获取财务指标"""
    indicator = db.query(Indicator).filter(Indicator.symbol == symbol).first()
    if not indicator:
        return StockDataResponse(
            symbol=symbol,
            data=[],
            available=False,
            reason="暂无数据"
        )
    return StockDataResponse(
        symbol=indicator.symbol,
        data=indicator.data,
        available=indicator.available,
        reason=indicator.reason,
        updated_at=indicator.updated_at
    )


@router.post("/indicator/{symbol}")
async def save_indicator(symbol: str, db: Session = Depends(get_db)):
    """保存财务指标"""
    from app.services.data.tushare_client import get_tushare_client
    tushare = get_tushare_client()
    
    if not tushare.is_connected:
        indicator = db.query(Indicator).filter(Indicator.symbol == symbol).first()
        if indicator:
            indicator.available = False
            indicator.reason = "Tushare Token 未配置"
            db.commit()
        return {"success": True, "available": False, "reason": "Tushare Token 未配置"}
    
    financial = get_financial_service()
    df = financial.get_fina_indicator(symbol, 4)
    
    if df is not None and not df.empty:
        data = df.to_dict('records')
        indicator = db.query(Indicator).filter(Indicator.symbol == symbol).first()
        if indicator:
            indicator.data = data
            indicator.available = True
            indicator.reason = None
        else:
            indicator = Indicator(symbol=symbol, data=data, available=True)
            db.add(indicator)
        db.commit()
        return {"success": True, "available": True}
    else:
        indicator = db.query(Indicator).filter(Indicator.symbol == symbol).first()
        if indicator:
            indicator.available = False
            indicator.reason = "未获取到数据"
            db.commit()
        return {"success": True, "available": False, "reason": "未获取到数据"}


# ===== Moneyflow 资金流向 =====

@router.get("/moneyflow/{symbol}", response_model=StockDataResponse)
async def get_moneyflow(symbol: str, db: Session = Depends(get_db)):
    """获取资金流向"""
    moneyflow = db.query(Moneyflow).filter(Moneyflow.symbol == symbol).first()
    if not moneyflow:
        return StockDataResponse(
            symbol=symbol,
            data=[],
            available=False,
            reason="暂无数据"
        )
    return StockDataResponse(
        symbol=moneyflow.symbol,
        data=moneyflow.data,
        available=moneyflow.available,
        reason=moneyflow.reason,
        updated_at=moneyflow.updated_at
    )


@router.post("/moneyflow/{symbol}")
async def save_moneyflow(symbol: str, days: int = 10, db: Session = Depends(get_db)):
    """保存资金流向"""
    from app.services.data.tushare_client import get_tushare_client
    tushare = get_tushare_client()
    
    if not tushare.is_connected:
        moneyflow = db.query(Moneyflow).filter(Moneyflow.symbol == symbol).first()
        if moneyflow:
            moneyflow.available = False
            moneyflow.reason = "Tushare Token 未配置"
            db.commit()
        return {"success": True, "available": False, "reason": "Tushare Token 未配置"}
    
    market = get_market_service()
    df = market.get_moneyflow(symbol, days)
    
    if df is not None and not df.empty:
        data = df.to_dict('records')
        moneyflow = db.query(Moneyflow).filter(Moneyflow.symbol == symbol).first()
        if moneyflow:
            moneyflow.data = data
            moneyflow.available = True
            moneyflow.reason = None
        else:
            moneyflow = Moneyflow(symbol=symbol, data=data, available=True)
            db.add(moneyflow)
        db.commit()
        return {"success": True, "available": True}
    else:
        moneyflow = db.query(Moneyflow).filter(Moneyflow.symbol == symbol).first()
        if moneyflow:
            moneyflow.available = False
            moneyflow.reason = "未获取到数据"
            db.commit()
        return {"success": True, "available": False, "reason": "未获取到数据"}


# ===== Margin 融资融券 =====

@router.get("/margin/{symbol}", response_model=StockDataResponse)
async def get_margin(symbol: str, db: Session = Depends(get_db)):
    """获取融资融券"""
    margin = db.query(Margin).filter(Margin.symbol == symbol).first()
    if not margin:
        return StockDataResponse(
            symbol=symbol,
            data=[],
            available=False,
            reason="暂无数据"
        )
    return StockDataResponse(
        symbol=margin.symbol,
        data=margin.data,
        available=margin.available,
        reason=margin.reason,
        updated_at=margin.updated_at
    )


@router.post("/margin/{symbol}")
async def save_margin(symbol: str, days: int = 10, db: Session = Depends(get_db)):
    """保存融资融券"""
    from app.services.data.tushare_client import get_tushare_client
    tushare = get_tushare_client()
    
    if not tushare.is_connected:
        margin = db.query(Margin).filter(Margin.symbol == symbol).first()
        if margin:
            margin.available = False
            margin.reason = "Tushare Token 未配置"
            db.commit()
        return {"success": True, "available": False, "reason": "Tushare Token 未配置"}
    
    market = get_market_service()
    df = market.get_margin(symbol, days)
    
    if df is not None and not df.empty:
        data = df.to_dict('records')
        margin = db.query(Margin).filter(Margin.symbol == symbol).first()
        if margin:
            margin.data = data
            margin.available = True
            margin.reason = None
        else:
            margin = Margin(symbol=symbol, data=data, available=True)
            db.add(margin)
        db.commit()
        return {"success": True, "available": True}
    else:
        margin = db.query(Margin).filter(Margin.symbol == symbol).first()
        if margin:
            margin.available = False
            margin.reason = "未获取到数据"
            db.commit()
        return {"success": True, "available": False, "reason": "未获取到数据"}


# ===== 批量查询所有数据 =====

@router.get("/query/{symbol}")
async def query_stock(symbol: str, db: Session = Depends(get_db)):
    """查询股票所有数据"""
    # 获取 Quote
    quote = db.query(Quote).filter(Quote.symbol == symbol).first()
    quote_data = None
    if quote and quote.available:
        quote_data = {"data": quote.data, "available": True}
    
    # 获取 Daily
    daily = db.query(Daily).filter(Daily.symbol == symbol).first()
    daily_data = None
    if daily and daily.available:
        daily_data = {"data": daily.data, "available": True}
    
    # 获取 Indicator
    indicator = db.query(Indicator).filter(Indicator.symbol == symbol).first()
    indicator_data = None
    if indicator and indicator.available:
        indicator_data = {"data": indicator.data, "available": True}
    
    # 获取 Moneyflow
    moneyflow = db.query(Moneyflow).filter(Moneyflow.symbol == symbol).first()
    moneyflow_data = None
    if moneyflow and moneyflow.available:
        moneyflow_data = {"data": moneyflow.data, "available": True}
    
    # 获取 Margin
    margin = db.query(Margin).filter(Margin.symbol == symbol).first()
    margin_data = None
    if margin and margin.available:
        margin_data = {"data": margin.data, "available": True}
    
    return {
        "symbol": symbol,
        "quote": quote_data,
        "daily": daily_data,
        "indicator": indicator_data,
        "moneyflow": moneyflow_data,
        "margin": margin_data
    }


@router.post("/query/{symbol}")
async def query_and_save_stock(symbol: str, db: Session = Depends(get_db)):
    """查询并保存股票所有数据"""
    from datetime import datetime, timedelta
    
    results = {}
    
    # 1. Quote
    stock = get_stock_service()
    data = stock.get_quote(symbol)
    if data:
        quote = db.query(Quote).filter(Quote.symbol == symbol).first()
        if quote:
            quote.data = data
            quote.available = True
        else:
            quote = Quote(symbol=symbol, data=data, available=True)
            db.add(quote)
        results["quote"] = True
    else:
        results["quote"] = False
    db.commit()
    
    # 2. Daily
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")
    df = stock.get_daily(symbol, start_date, end_date)
    if df is not None and not df.empty:
        from datetime import date
        data = []
        for record in df.to_dict('records'):
            processed = {}
            for key, value in record.items():
                if isinstance(value, (date,)):
                    processed[key] = value.strftime("%Y-%m-%d")
                else:
                    processed[key] = value
            data.append(processed)
        
        daily = db.query(Daily).filter(Daily.symbol == symbol).first()
        if daily:
            daily.data = data
            daily.available = True
        else:
            daily = Daily(symbol=symbol, data=data, available=True)
            db.add(daily)
        results["daily"] = True
    else:
        results["daily"] = False
    db.commit()
    
    # 3. Indicator
    from app.services.data.tushare_client import get_tushare_client
    tushare = get_tushare_client()
    if tushare.is_connected:
        financial = get_financial_service()
        df = financial.get_fina_indicator(symbol, 4)
        if df is not None and not df.empty:
            data = df.to_dict('records')
            indicator = db.query(Indicator).filter(Indicator.symbol == symbol).first()
            if indicator:
                indicator.data = data
                indicator.available = True
            else:
                indicator = Indicator(symbol=symbol, data=data, available=True)
                db.add(indicator)
            results["indicator"] = True
        else:
            results["indicator"] = False
    else:
        results["indicator"] = "no_token"
    db.commit()
    
    # 4. Moneyflow
    if tushare.is_connected:
        market = get_market_service()
        df = market.get_moneyflow(symbol, 10)
        if df is not None and not df.empty:
            data = df.to_dict('records')
            moneyflow = db.query(Moneyflow).filter(Moneyflow.symbol == symbol).first()
            if moneyflow:
                moneyflow.data = data
                moneyflow.available = True
            else:
                moneyflow = Moneyflow(symbol=symbol, data=data, available=True)
                db.add(moneyflow)
            results["moneyflow"] = True
        else:
            results["moneyflow"] = False
    else:
        results["moneyflow"] = "no_token"
    db.commit()
    
    # 5. Margin
    if tushare.is_connected:
        market = get_market_service()
        df = market.get_margin(symbol, 10)
        if df is not None and not df.empty:
            data = df.to_dict('records')
            margin = db.query(Margin).filter(Margin.symbol == symbol).first()
            if margin:
                margin.data = data
                margin.available = True
            else:
                margin = Margin(symbol=symbol, data=data, available=True)
                db.add(margin)
            results["margin"] = True
        else:
            results["margin"] = False
    else:
        results["margin"] = "no_token"
    db.commit()
    
    return {"success": True, "symbol": symbol, "results": results}


# ===== BaoStock 新增功能 =====

try:
    from app.services.stock_data.factory import get_stock_provider
    BAOSTOCK_FACTORY_AVAILABLE = True
except Exception:
    BAOSTOCK_FACTORY_AVAILABLE = False


@router.get("/info")
async def get_stock_info(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("baostock", description="数据源")
):
    """获取股票详细信息"""
    if not BAOSTOCK_FACTORY_AVAILABLE:
        raise HTTPException(status_code=500, detail="Stock data service not available")
    
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
        return {"data": info, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No info data for {symbol}")


@router.get("/valuation")
async def get_stock_valuation(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("baostock", description="数据源"),
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD")
):
    """获取估值数据（PE、PB等）"""
    if not BAOSTOCK_FACTORY_AVAILABLE:
        raise HTTPException(status_code=500, detail="Stock data service not available")
    
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
        return {"data": valuation, "cached": False}
    
    raise HTTPException(status_code=404, detail=f"No valuation data for {symbol}")
