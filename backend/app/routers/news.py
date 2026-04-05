"""
新闻 API 路由
"""
import logging
from fastapi import APIRouter, Query, HTTPException
from app.services.logging_manager import get_logger

logger = get_logger("news.router")

try:
    from app.services.news.aggregator import get_news_aggregator
    AGGREGATOR_AVAILABLE = True
except Exception as e:
    logger.error(f"Failed to import news modules: {e}")
    AGGREGATOR_AVAILABLE = False
    get_news_aggregator = None

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/sources")
async def get_news_sources():
    """获取可用的新闻源"""
    return {
        "sources": [
            {"id": "eastmoney", "name": "东方财富", "description": "A股/港股新闻"},
            {"id": "finnhub", "name": "FinnHub", "description": "美股新闻"},
            {"id": "alpha_vantage", "name": "Alpha Vantage", "description": "国际市场新闻"},
            {"id": "auto", "name": "自动选择", "description": "自动选择可用新闻源"},
        ]
    }


@router.get("/stock")
async def get_stock_news(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("auto", description="新闻源"),
    hours_back: int = Query(24, description="回溯小时数"),
    max_news: int = Query(10, description="最大新闻数")
):
    """获取股票新闻"""
    aggregator = get_news_aggregator()
    
    news = await aggregator.get_stock_news(
        symbol=symbol,
        provider=provider,
        hours_back=hours_back,
        max_news=max_news
    )
    
    return {
        "symbol": symbol,
        "provider": provider,
        "news": news,
        "count": len(news)
    }


@router.get("/report")
async def get_news_report(
    symbol: str = Query(..., description="股票代码"),
    provider: str = Query("auto", description="新闻源"),
    hours_back: int = Query(24, description="回溯小时数"),
    max_news: int = Query(10, description="最大新闻数")
):
    """获取格式化后的新闻报告"""
    aggregator = get_news_aggregator()
    
    news = await aggregator.get_stock_news(
        symbol=symbol,
        provider=provider,
        hours_back=hours_back,
        max_news=max_news
    )
    
    report = aggregator.format_news_report(news, symbol)
    
    return {
        "symbol": symbol,
        "report": report,
        "count": len(news)
    }
