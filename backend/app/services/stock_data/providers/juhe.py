"""
聚合数据 (Juhe) 股票数据提供者
基于 AlphaCouncil 的 juheService.ts 实现
"""
import os
import asyncio
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date
import logging

from .base import BaseStockProvider
from app.services.logging_manager import get_logger

logger = get_logger("stock_data.juhe")

JUHE_BASE_URL = "http://web.juhe.cn/finance/stock/hs"
DEFAULT_JUHE_API_KEY = "89498102bf59b7e7bee98e62a3b2d230"


class JuheProvider(BaseStockProvider):
    """聚合数据 (Juhe) 股票数据提供者"""

    def __init__(self, api_key: str = None, config: Dict[str, Any] = None):
        super().__init__("Juhe")
        self.api_key = api_key or os.getenv("JUHE_API_KEY", DEFAULT_JUHE_API_KEY)
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30)
        self._raw_data_cache: Dict[str, Any] = {}

    async def connect(self) -> bool:
        """验证 API Key 是否有效"""
        if not self.api_key:
            self.logger.error("Juhe API key not configured")
            return False

        try:
            test_result = await self._fetch_data("sh600519")
            if test_result and test_result.get("success"):
                self.connected = True
                self.logger.info("Juhe API connected successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Juhe connection failed: {e}")
            return False

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def get_stock_basic(self, symbol: str = None) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """获取股票基本信息"""
        if not symbol:
            return None

        try:
            data = await self._fetch_data(symbol)
            if data and data.get("success"):
                raw = data.get("data", {}).get("data", {})
                return {
                    "code": raw.get("gid", ""),
                    "name": raw.get("name", ""),
                    "symbol": self._normalize_symbol(raw.get("gid", "")),
                    "full_symbol": raw.get("gid", "").upper(),
                    "data_source": "juhe"
                }
        except Exception as e:
            self.logger.error(f"Failed to get stock basic: {e}")
        return None

    async def get_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情"""
        self.logger.warning(f"=== Juhe get_quotes called for {symbol} ===")
        try:
            data = await self._fetch_data(symbol)
            if data and data.get("success"):
                raw = data.get("data", {}).get("data", {})
                gopicture = data.get("data", {}).get("gopicture", {})
                self.logger.info(f"gopicture received in get_quotes: {gopicture}")
                return self.standardize_quotes(raw, gopicture)
        except Exception as e:
            self.logger.error(f"Failed to get quotes: {e}")
        return None

    async def get_historical(
        self,
        symbol: str,
        start_date: Union[str, date],
        end_date: Union[str, date] = None,
        period: str = "daily"
    ):
        """获取历史数据 - Juhe 不支持，返回 None"""
        self.logger.warning("Juhe provider does not support historical data")
        return None

    async def get_financial(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取财务数据 - Juhe 不支持"""
        return None

    def get_order_book(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取五档买卖盘口 (直接从缓存获取)"""
        return self._raw_data_cache.get(symbol, {}).get("order_book")

    def get_market_index(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取大盘指数数据"""
        return self._raw_data_cache.get(symbol, {}).get("market_index")

    async def get_index_quote(self, index_type: int = 0) -> Optional[Dict[str, Any]]:
        """
        获取指数行情
        
        Args:
            index_type: 0=上证综合指数, 1=深证成指
        """
        import httpx
        
        url = f"{JUHE_BASE_URL}?type={index_type}&key={self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data.get("error_code") != 0:
                    self.logger.error(f"Juhe index API error: {data.get('reason')}")
                    return None
                
                result = data.get("result", {})
                if not result:
                    return None
                
                index_data = result if isinstance(result, dict) else result[0] if result else {}
                
                return self._standardize_index(index_data, index_type)
                
        except Exception as e:
            self.logger.error(f"Failed to fetch index from Juhe: {e}")
            return None

    def _standardize_index(self, raw_data: Dict[str, Any], index_type: int) -> Dict[str, Any]:
        """标准化指数数据"""
        return {
            "type": "shanghai" if index_type == 0 else "shenzhen",
            "name": raw_data.get("name", "上证指数" if index_type == 0 else "深证成指"),
            "close": self._convert_to_float(raw_data.get("nowpri")),
            "open": self._convert_to_float(raw_data.get("openPri")),
            "high": self._convert_to_float(raw_data.get("highPri")),
            "low": self._convert_to_float(raw_data.get("lowpri")),
            "pre_close": self._convert_to_float(raw_data.get("yesPri")),
            "change": self._convert_to_float(raw_data.get("increase")),
            "pct_chg": self._convert_to_float(raw_data.get("increPer")),
            "volume": self._convert_to_float(raw_data.get("dealNum")),
            "amount": self._convert_to_float(raw_data.get("dealPri")),
            "time": raw_data.get("time"),
            "data_source": "juhe",
            "now_pic": self._convert_to_float(raw_data.get("nowPic"))
        }

    async def _fetch_data(self, symbol: str) -> Dict[str, Any]:
        """调用 Juhe API 获取数据"""
        import httpx

        gid = self._normalize_gid(symbol)
        url = f"{JUHE_BASE_URL}?gid={gid}&key={self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if data.get("resultcode") != "200":
                    self.logger.error(f"Juhe API error: {data.get('reason')}")
                    return {"success": False, "error": data.get("reason")}

                result = data.get("result", [{}])[0] if data.get("result") else {}
                stock_data = result.get("data", {})
                dapan_data = result.get("dapandata")
                gopicture = result.get("gopicture")

                order_book = self._extract_order_book(stock_data)
                market_index = self._extract_market_index(dapan_data)

                self._raw_data_cache[symbol] = {
                    "data": stock_data,
                    "order_book": order_book,
                    "market_index": market_index,
                    "gopicture": gopicture
                }

                return {
                    "success": True,
                    "data": {
                        "data": stock_data,
                        "dapandata": dapan_data,
                        "gopicture": gopicture
                    }
                }
        except Exception as e:
            self.logger.error(f"Failed to fetch data from Juhe: {e}")
            return {"success": False, "error": str(e)}

    def _normalize_gid(self, symbol: str) -> str:
        """标准化股票代码为 Juhe 格式"""
        symbol = symbol.strip().lower()
        if not symbol.startswith("sh") and not symbol.startswith("sz"):
            if symbol.startswith("6"):
                symbol = f"sh{symbol}"
            else:
                symbol = f"sz{symbol}"
        return symbol

    def _normalize_symbol(self, gid: str) -> str:
        """从 gid 提取纯数字代码"""
        return gid.replace("sh", "").replace("sz", "") if gid else ""

    def _extract_order_book(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取五档买卖盘口"""
        return {
            "buy": [
                {"price": data.get("buyOnePri"), "volume": data.get("buyOne")},
                {"price": data.get("buyTwoPri"), "volume": data.get("buyTwo")},
                {"price": data.get("buyThreePri"), "volume": data.get("buyThree")},
                {"price": data.get("buyFourPri"), "volume": data.get("buyFour")},
                {"price": data.get("buyFivePri"), "volume": data.get("buyFive")},
            ],
            "sell": [
                {"price": data.get("sellOnePri"), "volume": data.get("sellOne")},
                {"price": data.get("sellTwoPri"), "volume": data.get("sellTwo")},
                {"price": data.get("sellThreePri"), "volume": data.get("sellThree")},
                {"price": data.get("sellFourPri"), "volume": data.get("sellFour")},
                {"price": data.get("sellFivePri"), "volume": data.get("sellFive")},
            ]
        }

    def _extract_market_index(self, dapan_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """提取大盘指数数据"""
        if not dapan_data:
            return None
        return {
            "name": dapan_data.get("name"),
            "point": dapan_data.get("dot"),
            "change": dapan_data.get("rate"),
            "volume": dapan_data.get("traNumber"),
            "amount": dapan_data.get("traAmount"),
            "now_pic": dapan_data.get("nowPic")
        }

    def standardize_quotes(self, raw_data: Dict[str, Any], gopicture: Dict[str, Any] = None) -> Dict[str, Any]:
        """标准化行情数据"""
        current_price = self._convert_to_float(raw_data.get("nowPri"))
        today_max = self._convert_to_float(raw_data.get("todayMax"))
        today_min = self._convert_to_float(raw_data.get("todayMin"))

        daily_amplitude = 0
        if current_price and today_max and today_min:
            daily_amplitude = ((today_max - today_min) / current_price) * 100

        symbol = self._normalize_symbol(raw_data.get("gid", ""))
        
        # 提取K线图URL
        if gopicture is None:
            gopicture = raw_data.get("gopicture", {})
        
        self.logger.info(f"standardize_quotes gopicture: {gopicture}")

        return {
            "symbol": symbol,
            "full_symbol": raw_data.get("gid", "").upper(),
            "name": raw_data.get("name", ""),
            "close": current_price,
            "open": self._convert_to_float(raw_data.get("todayStartPri")),
            "high": today_max,
            "low": today_min,
            "pre_close": self._convert_to_float(raw_data.get("yestodEndPri")),
            "change": self._convert_to_float(raw_data.get("increase")),
            "pct_chg": self._convert_to_float(raw_data.get("increPer")),
            "volume": self._convert_to_float(raw_data.get("traNumber")),
            "amount": self._convert_to_float(raw_data.get("traAmount")),
            "date": raw_data.get("date"),
            "time": raw_data.get("time"),
            "trade_date": raw_data.get("date"),
            "daily_amplitude": round(daily_amplitude, 2),
            # 补充字段
            "competitive_price": self._convert_to_float(raw_data.get("competitivePri")),  # 竞买价
            "reserve_price": self._convert_to_float(raw_data.get("reservePri")),       # 竞卖价
            "price_change_vol": self._convert_to_float(raw_data.get("nowPic")),      # 涨量
            # K线图URL
            "kline": {
                "min": gopicture.get("minurl") if gopicture else None,
                "day": gopicture.get("dayurl") if gopicture else None,
                "week": gopicture.get("weekurl") if gopicture else None,
                "month": gopicture.get("monthurl") if gopicture else None
            },
            "order_book": self._extract_order_book(raw_data),
            "market_index": self._extract_market_index(raw_data.get("dapandata")),
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "juhe"
        }


def format_stock_data_for_prompt(data: Optional[Dict[str, Any]], include_order_book: bool = True) -> str:
    """
    将原始数据格式化为 AI 可读的字符串
    基于 AlphaCouncil 的 formatStockDataForPrompt 实现

    Args:
        data: 标准化的股票数据 (来自 get_quotes)
        include_order_book: 是否包含五档盘口数据
    """
    if not data:
        return "无法获取实时行情数据 (API连接失败)，请依赖您的内部知识库或搜索工具。"

    current_price = data.get("close", 0)
    open_price = data.get("open", 0)
    high = data.get("high", 0)
    low = data.get("low", 0)
    pct_chg = data.get("pct_chg", 0)
    change = data.get("change", 0)
    volume = data.get("volume", 0)
    amount = data.get("amount", 0)
    daily_amplitude = data.get("daily_amplitude", 0)

    volume_str = f"{volume / 10000:.2f}万手" if volume > 10000 else f"{volume:.0f}手"
    amount_str = f"{amount / 100000000:.2f}亿元" if amount > 100000000 else f"{amount / 10000:.2f}万元"

    liquidity = "充足" if amount > 100000000 else "一般" if amount > 50000000 else "偏弱"

    market_index = data.get("market_index")
    market_index_info = ""
    if market_index:
        change_val = float(market_index.get("change", 0))
        market_index_info = f"""
【大盘指数】
  指数名称: {market_index.get('name')}
  当前点位: {market_index.get('point')}
  涨跌幅度: {'+' if change_val >= 0 else ''}{change_val}%
  成交量: {market_index.get('volume')}万手
  成交额: {market_index.get('amount')}亿元"""

    order_book_info = ""
    if include_order_book and data.get("order_book"):
        ob = data["order_book"]
        buy = ob.get("buy", [])
        sell = ob.get("sell", [])

        def format_line(price, vol, label):
            p = price if price else "-"
            v = vol if vol else "-"
            return f"  │ {label}  ¥{str(p):>8} │ {str(v):>10}手 │"

        order_book_info = f"""
【五档盘口】（关键数据：研判买卖力量对比）
  ┌─────────────────────────────────────┐"""

        sell_rows = []
        for i in range(4, -1, -1):
            if i < len(sell):
                sell_rows.append(format_line(sell[i].get("price"), sell[i].get("volume"), f"卖{i+1}"))
        order_book_info += "\n" + "\n".join(sell_rows)

        sell_one_price = sell[0].get('price') if sell and sell[0].get('price') else '-'
        sell_one_vol = sell[0].get('volume') if sell and sell[0].get('volume') else '-'
        order_book_info += f"""
  │ 卖一  ¥{str(sell_one_price):>8} │ {str(sell_one_vol):>10}手 │ ⬅️ 压力
  ├─────────────────────────────────────┤"""

        buy_rows = []
        for i in range(5):
            if i < len(buy):
                label = "买一" if i == 0 else f"买{i+1}"
                buy_rows.append(format_line(buy[i].get("price"), buy[i].get("volume"), label))
        order_book_info += "\n" + "\n".join(buy_rows)

        order_book_info += """
  └─────────────────────────────────────┘

💡 分析提示: 请重点关注盘口买卖挂单量差异，判断主力意图"""

    return f"""
╔═══════════════════════════════════════════════════════════╗
║           实时行情数据 (来源: 聚合数据API)                ║
╚═══════════════════════════════════════════════════════════╝

【基本信息】
  股票名称: {data.get('name')}
  股票代码: {data.get('full_symbol')}
  数据时间: {data.get('date')} {data.get('time')}

【价格信息】
  当前价格: ¥{current_price}
  涨跌幅度: {'+' if pct_chg >= 0 else ''}{pct_chg}%
  涨跌金额: {'+' if change >= 0 else ''}¥{change}
  今日开盘: ¥{open_price}
  昨日收盘: ¥{data.get('pre_close')}
  今日最高: ¥{high}
  今日最低: ¥{low}

【成交情况】
  成交量: {volume_str}
  成交额: {amount_str}
  日振幅: {daily_amplitude}%
  流动性: {liquidity}{market_index_info}
{order_book_info}
═══════════════════════════════════════════════════════════
"""
