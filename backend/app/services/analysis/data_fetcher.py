"""
股票数据获取与格式化
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.services.logging_manager import get_logger

logger = get_logger("analysis.data_fetcher")


class StockDataFetcher:
    """股票数据获取器"""
    
    def __init__(self, provider: str = "juhe"):
        self.provider = provider
        self._provider = None
        self._cache_service = None
    
    async def _get_provider(self):
        """获取数据提供者"""
        if self._provider is None:
            try:
                from app.services.stock_data.factory import get_stock_provider
                self._provider = get_stock_provider(self.provider)
                if self._provider and not self._provider.connected:
                    await self._provider.connect()
            except Exception as e:
                logger.error(f"Failed to get stock provider: {e}")
        return self._provider
    
    async def fetch_all_data(self, symbol: str) -> Dict[str, Any]:
        """获取所有需要的股票数据"""
        provider = await self._get_provider()
        if not provider:
            return {"error": "Failed to connect to stock provider"}
        
        # 获取多个数据
        data = {}
        
        # 1. 实时行情
        try:
            quote = await provider.get_quotes(symbol)
            if quote:
                data["quote"] = self.format_quote(quote)
        except Exception as e:
            logger.error(f"Failed to fetch quote: {e}")
            data["quote"] = {"error": str(e)}
        
        # 2. 日K线数据 (最近30天)
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            daily = await provider.get_historical(
                symbol, 
                start_date=start_date, 
                end_date=end_date,
                period="daily"
            )
            if daily:
                data["daily"] = self.format_daily(daily)
        except Exception as e:
            logger.error(f"Failed to fetch daily: {e}")
        
        # 3. 财务指标
        try:
            indicator = await provider.get_financial(symbol)
            if indicator:
                data["financial"] = self.format_financial(indicator)
        except Exception as e:
            logger.error(f"Failed to fetch financial: {e}")
        
        # 4. 估值数据
        try:
            valuation = await provider.get_valuation(symbol)
            if valuation:
                data["valuation"] = valuation
        except Exception as e:
            logger.error(f"Failed to fetch valuation: {e}")
        
        # 5. 资金流向
        try:
            moneyflow = await provider.get_moneyflow(symbol, days=5)
            if moneyflow:
                data["moneyflow"] = moneyflow
        except Exception as e:
            logger.error(f"Failed to fetch moneyflow: {e}")
        
        # 6. 融资融券
        try:
            margin = await provider.get_margin(symbol, days=5)
            if margin:
                data["margin"] = margin
        except Exception as e:
            logger.error(f"Failed to fetch margin: {e}")
        
        # 7. 大盘指数
        try:
            index_sh = await provider.get_index_quote(0)  # 上证
            index_sz = await provider.get_index_quote(1)   # 深证
            data["index"] = {
                "shanghai": index_sh,
                "shenzhen": index_sz
            }
        except Exception as e:
            logger.error(f"Failed to fetch index: {e}")
        
        # 8. 简化的五档盘口
        if "quote" in data and "order_book" in data["quote"]:
            data["order_book"] = data["quote"]["order_book"]
        
        return data
    
    def format_quote(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """格式化实时行情"""
        if not quote:
            return {}
        
        return {
            "symbol": quote.get("symbol"),
            "name": quote.get("name"),
            "current_price": quote.get("close"),
            "open": quote.get("open"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "pre_close": quote.get("pre_close"),
            "change": quote.get("change"),
            "pct_chg": quote.get("pct_chg"),
            "volume": quote.get("volume"),
            "amount": quote.get("amount"),
            "date": quote.get("date"),
            "time": quote.get("time"),
            "order_book": quote.get("order_book"),
            "kline": quote.get("kline")
        }
    
    def format_daily(self, daily: Any) -> str:
        """格式化日K线数据为文本"""
        if not daily:
            return "无日K线数据"
        
        lines = ["=== 最近30个交易日 ==="]
        
        # 如果是DataFrame
        if hasattr(daily, 'tail'):
            df = daily.tail(30)
            for _, row in df.iterrows():
                date = row.get('date', row.get('trade_date', ''))
                open_p = row.get('open', '')
                high = row.get('high', '')
                low = row.get('low', '')
                close = row.get('close', '')
                vol = row.get('volume', '')
                lines.append(f"{date}: 开{open_p} 高{high} 低{low} 收{close} 量{vol}")
        elif isinstance(daily, list):
            for item in daily[-30:]:
                lines.append(str(item))
        
        return "\n".join(lines)
    
    def format_financial(self, financial: Any) -> str:
        """格式化财务数据"""
        if not financial:
            return "无财务数据"
        
        lines = ["=== 财务数据 ==="]
        
        if isinstance(financial, dict):
            for key, value in financial.items():
                if isinstance(value, dict):
                    lines.append(f"\n{key}:")
                    for k, v in value.items():
                        lines.append(f"  {k}: {v}")
                else:
                    lines.append(f"{key}: {value}")
        elif hasattr(financial, 'tail'):
            df = financial.tail(5)
            for _, row in df.iterrows():
                lines.append(str(row.to_dict()))
        
        return "\n".join(lines)
    
    def format_for_agent(self, agent_name: str, data: Dict[str, Any]) -> str:
        """为特定智能体格式化数据"""
        lines = []
        
        if agent_name == "fundamental":
            # 基本面分析 - 需要 quote, financial, valuation
            if "quote" in data:
                q = data["quote"]
                lines.append("=== 实时行情 ===")
                lines.append(f"股票: {q.get('name')} ({q.get('symbol')})")
                lines.append(f"当前价格: {q.get('current_price')}")
                lines.append(f"涨跌幅: {q.get('pct_chg')}%")
                lines.append(f"成交量: {q.get('volume')}")
                lines.append(f"成交额: {q.get('amount')}")
                lines.append(f"今开: {q.get('open')}, 最高: {q.get('high')}, 最低: {q.get('low')}")
                lines.append(f"昨收: {q.get('pre_close')}")
            
            if "financial" in data:
                lines.append(f"\n{data['financial']}")
            
            if "valuation" in data:
                lines.append(f"\n=== 估值数据 ===")
                lines.append(str(data["valuation"]))
        
        elif agent_name == "technical":
            # 技术分析 - 需要 quote, daily, order_book
            if "quote" in data:
                q = data["quote"]
                lines.append("=== 实时行情 ===")
                lines.append(f"当前价格: {q.get('current_price')}")
                lines.append(f"今日振幅: {((q.get('high', 0) - q.get('low', 0)) / q.get('current_price', 1) * 100):.2f}%" if q.get('current_price') else "N/A")
                lines.append(f"成交量: {q.get('volume')}")
                lines.append(f"最高: {q.get('high')}, 最低: {q.get('low')}")
                lines.append(f"今开: {q.get('open')}")
            
            if "daily" in data:
                lines.append(f"\n{data['daily']}")
            
            if "order_book" in data and data["order_book"]:
                lines.append("\n=== 五档买卖盘口 ===")
                ob = data["order_book"]
                if "buy" in ob:
                    lines.append("买盘:")
                    for i, b in enumerate(ob["buy"][:3], 1):
                        lines.append(f"  买{i}: {b.get('price')} x {b.get('volume')}")
                if "sell" in ob:
                    lines.append("卖盘:")
                    for i, s in enumerate(ob["sell"][:3], 1):
                        lines.append(f"  卖{i}: {s.get('price')} x {s.get('volume')}")
        
        elif agent_name == "risk":
            # 风控分析 - 需要 quote, moneyflow, margin, index
            if "quote" in data:
                q = data["quote"]
                lines.append("=== 实时行情 ===")
                lines.append(f"当前价格: {q.get('current_price')}")
                lines.append(f"涨跌幅: {q.get('pct_chg')}%")
                lines.append(f"成交量: {q.get('volume')}")
                lines.append(f"成交额: {q.get('amount')}")
            
            if "moneyflow" in data:
                lines.append(f"\n=== 资金流向 ===")
                lines.append(str(data["moneyflow"]))
            
            if "margin" in data:
                lines.append(f"\n=== 融资融券 ===")
                lines.append(str(data["margin"]))
            
            if "index" in data:
                idx = data["index"]
                lines.append(f"\n=== 大盘指数 ===")
                if idx.get("shanghai"):
                    sh = idx["shanghai"]
                    lines.append(f"上证指数: {sh.get('close')} ({sh.get('pct_chg')}%)")
                if idx.get("shenzhen"):
                    sz = idx["shenzhen"]
                    lines.append(f"深证成指: {sz.get('close')} ({sz.get('pct_chg')}%)")
        
        return "\n".join(lines) if lines else "无数据"


async def fetch_stock_data(symbol: str, provider: str = "juhe") -> Dict[str, Any]:
    """便捷函数：获取股票数据"""
    fetcher = StockDataFetcher(provider)
    return await fetcher.fetch_all_data(symbol)
