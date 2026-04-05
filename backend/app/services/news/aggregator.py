"""
新闻聚合服务
"""
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.services.stock_data.factory import get_stock_provider
from app.services.logging_manager import get_logger

logger = get_logger("news.aggregator")


class NewsAggregator:
    """新闻聚合器 - 整合多个新闻源"""
    
    def __init__(self):
        self.finnhub_key = os.getenv("FINNHUB_API_KEY")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
    
    async def get_stock_news(
        self,
        symbol: str,
        provider: str = "auto",
        hours_back: int = 24,
        max_news: int = 10
    ) -> List[Dict[str, Any]]:
        """获取股票新闻"""
        all_news = []
        
        if provider == "auto" or provider == "eastmoney":
            news = await self._get_eastmoney_news(symbol, max_news)
            all_news.extend(news)
        
        if provider == "auto" or provider == "finnhub":
            if self.finnhub_key:
                news = await self._get_finnhub_news(symbol, hours_back, max_news)
                all_news.extend(news)
        
        if provider == "auto" or provider == "alpha_vantage":
            if self.alpha_vantage_key:
                news = await self._get_alpha_vantage_news(symbol, hours_back, max_news)
                all_news.extend(news)
        
        unique_news = self._deduplicate_news(all_news)
        sorted_news = sorted(
            unique_news,
            key=lambda x: x.get("publish_time", ""),
            reverse=True
        )
        
        return sorted_news[:max_news]
    
    async def _get_eastmoney_news(self, symbol: str, max_news: int) -> List[Dict[str, Any]]:
        """获取东方财富新闻"""
        try:
            provider = get_stock_provider("akshare")
            if not provider:
                return []
            
            await provider.connect()
            news = await provider.get_news(symbol, max_news=max_news)
            
            if news:
                return news
            return []
        except Exception as e:
            logger.warning(f"Eastmoney news failed: {e}")
            return []
    
    async def _get_finnhub_news(self, symbol: str, hours_back: int, max_news: int) -> List[Dict[str, Any]]:
        """获取 FinnHub 新闻"""
        if not self.finnhub_key:
            return []
        
        try:
            import requests
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            url = "https://finnhub.io/api/v1/company-news"
            params = {
                "symbol": symbol,
                "from": start_time.strftime("%Y-%m-%d"),
                "to": end_time.strftime("%Y-%m-%d"),
                "token": self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_list = []
            
            for item in data[:max_news]:
                news_list.append({
                    "title": item.get("headline", ""),
                    "content": item.get("summary", ""),
                    "source": item.get("source", "FinnHub"),
                    "publish_time": datetime.fromtimestamp(item.get("datetime", 0)).isoformat(),
                    "url": item.get("url", ""),
                    "data_source": "finnhub"
                })
            
            return news_list
            
        except Exception as e:
            logger.warning(f"FinnHub news failed: {e}")
            return []
    
    async def _get_alpha_vantage_news(self, symbol: str, hours_back: int, max_news: int) -> List[Dict[str, Any]]:
        """获取 Alpha Vantage 新闻"""
        if not self.alpha_vantage_key:
            return []
        
        try:
            import requests
            
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": symbol,
                "apikey": self.alpha_vantage_key,
                "limit": max_news
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_list = []
            
            if "feed" in data:
                for item in data["feed"][:max_news]:
                    time_str = item.get("time_published", "")
                    try:
                        publish_time = datetime.strptime(time_str, "%Y%m%dT%H%M%S").isoformat()
                    except:
                        publish_time = datetime.now().isoformat()
                    
                    news_list.append({
                        "title": item.get("title", ""),
                        "content": item.get("summary", ""),
                        "source": item.get("source", "Alpha Vantage"),
                        "publish_time": publish_time,
                        "url": item.get("url", ""),
                        "data_source": "alpha_vantage"
                    })
            
            return news_list
            
        except Exception as e:
            logger.warning(f"Alpha Vantage news failed: {e}")
            return []
    
    def _deduplicate_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """新闻去重"""
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            title = news.get("title", "").lower().strip()
            if title and title not in seen_titles and len(title) > 10:
                seen_titles.add(title)
                unique_news.append(news)
        
        return unique_news
    
    def format_news_report(self, news_list: List[Dict[str, Any]], symbol: str) -> str:
        """格式化新闻报告"""
        if not news_list:
            return f"未获取到 {symbol} 的新闻数据。"
        
        report = f"# {symbol} 新闻报告\n\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"新闻总数: {len(news_list)}条\n\n"
        
        for i, news in enumerate(news_list[:10], 1):
            report += f"## {i}. {news.get('title', '')}\n"
            report += f"来源: {news.get('source', '')} | 时间: {news.get('publish_time', '')}\n"
            report += f"{news.get('content', '')}\n\n"
        
        return report


_news_aggregator = None


def get_news_aggregator() -> NewsAggregator:
    global _news_aggregator
    if _news_aggregator is None:
        _news_aggregator = NewsAggregator()
    return _news_aggregator
