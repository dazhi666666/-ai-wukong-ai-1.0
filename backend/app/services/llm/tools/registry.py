"""
工具注册表 - 统一管理所有股票数据获取工具
"""
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
from app.services.logging_manager import get_logger

logger = get_logger("tool_registry")


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class ToolDefinition:
    """工具定义"""
    tool_id: str
    name: str
    description: str
    category: str
    data_source: str
    timeout: int = 30
    is_enabled: bool = True
    is_online: bool = True
    parameters: List[ToolParameter] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    icon: str = "📊"
    
    def to_dict(self) -> dict:
        return {
            **asdict(self),
            'parameters': [asdict(p) for p in self.parameters]
        }


@dataclass
class ToolCategory:
    """工具分类定义"""
    id: str
    name: str
    description: str
    color: str
    icon: str
    order: int = 0


DEFAULT_CATEGORIES = [
    ToolCategory("juhe", "Juhe 聚合数据", "聚合数据 API，提供实时行情和历史数据", "#f59e0b", "🔷", 1),
    ToolCategory("tushare", "Tushare", "Tushare Pro API，提供行情、财务、资金等全面数据", "#3b82f6", "🔶", 2),
    ToolCategory("akshare", "AKShare", "AKShare 开源财经数据接口", "#10b981", "🔹", 3),
    ToolCategory("baostock", "BaoStock", "BaoStock 证券数据接口", "#ec4899", "🔸", 4),
    ToolCategory("other", "其它", "其他数据源工具", "#6b7280", "📊", 5),
]


# 数据源映射 - 用于从工具名推断数据源
SOURCE_MAPPING = {
    'juhe': 'juhe',
    'tushare': 'tushare',
    'akshare': 'akshare',
    'baostock': 'baostock',
}

def _infer_data_source(tool_id: str) -> str:
    """从工具ID推断数据源"""
    tool_id_lower = tool_id.lower()
    for key, source in SOURCE_MAPPING.items():
        if key in tool_id_lower:
            return source
    return 'other'


class ToolRegistry:
    """工具注册表管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[str, ToolCategory] = {}
        self._tool_functions: Dict[str, Any] = {}
        self._enabled_tools: set = set()
        
        for cat in DEFAULT_CATEGORIES:
            self._categories[cat.id] = cat
        
        self._register_default_tools()
        
        # 从数据库加载启用的工具
        self._load_enabled_from_database()
    
    def _load_enabled_from_database(self):
        """从数据库加载启用的工具"""
        try:
            enabled_ids = self._load_enabled_tools_from_db()
            if enabled_ids:
                self._enabled_tools = set(enabled_ids)
                for tool_id, tool in self._tools.items():
                    tool.is_enabled = tool_id in self._enabled_tools
                logger.info(f"Loaded {len(enabled_ids)} enabled tools from database")
            else:
                # 如果数据库没有配置，默认启用前5个工具
                default_enabled = list(self._tools.keys())[:5]
                self._enabled_tools = set(default_enabled)
                for tool_id, tool in self._tools.items():
                    tool.is_enabled = tool_id in self._enabled_tools
                logger.info(f"No enabled tools in DB, using default: {default_enabled}")
        except Exception as e:
            logger.warning(f"Failed to load enabled tools from DB: {e}")
            # 使用默认
            default_enabled = list(self._tools.keys())[:5]
            self._enabled_tools = set(default_enabled)
    
    def _register_default_tools(self):
        """注册默认工具"""
        default_tools = [
            ToolDefinition(
                tool_id="get_stock_quote",
                name="📈 统一市场数据",
                description="获取统一格式的股票市场数据，支持实时行情",
                category="market",
                data_source="yfinance/tushare",
                timeout=30,
                icon="📈",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码（支持A股、港股、美股）", True),
                ]
            ),
            ToolDefinition(
                tool_id="get_stock_daily",
                name="📊 历史日线数据",
                description="获取股票历史日线数据",
                category="market",
                data_source="yfinance/tushare",
                timeout=30,
                icon="📊",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码", True),
                    ToolParameter("start_date", "string", "开始日期 (YYYY-MM-DD)", True),
                    ToolParameter("end_date", "string", "结束日期 (YYYY-MM-DD)", True),
                ]
            ),
            ToolDefinition(
                tool_id="get_index_quote",
                name="📈 指数行情",
                description="获取指数实时行情数据",
                category="market",
                data_source="tushare",
                timeout=30,
                icon="📈",
                parameters=[
                    ToolParameter("index_code", "string", "指数代码，如 000001、399001", True),
                ]
            ),
            ToolDefinition(
                tool_id="get_fina_indicator",
                name="📊 财务指标",
                description="获取股票财务指标数据",
                category="fundamentals",
                data_source="tushare",
                timeout=30,
                icon="📊",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码", True),
                    ToolParameter("periods", "int", "获取报告期数量，默认4个", False, 4),
                ]
            ),
            ToolDefinition(
                tool_id="get_moneyflow",
                name="💰 资金流向",
                description="获取股票资金流向数据",
                category="market",
                data_source="tushare",
                timeout=30,
                icon="💰",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码", True),
                    ToolParameter("days", "int", "获取天数，默认10天", False, 10),
                ]
            ),
            ToolDefinition(
                tool_id="get_margin",
                name="💳 融资融券",
                description="获取融资融券数据",
                category="market",
                data_source="tushare",
                timeout=30,
                icon="💳",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码", True),
                    ToolParameter("days", "int", "获取天数，默认10天", False, 10),
                ]
            ),
            ToolDefinition(
                tool_id="get_leaderboard",
                name="🐉 龙虎榜",
                description="获取龙虎榜数据",
                category="market",
                data_source="tushare",
                timeout=30,
                icon="🐉",
                parameters=[
                    ToolParameter("date", "string", "日期，格式YYYYMMDD，默认最新", False),
                ]
            ),
            ToolDefinition(
                tool_id="get_etf_spot",
                name="📑 ETF行情",
                description="获取ETF实时行情",
                category="market",
                data_source="tushare",
                timeout=30,
                icon="📑",
                parameters=[
                    ToolParameter("limit", "int", "返回数量，默认20", False, 20),
                ]
            ),
            ToolDefinition(
                tool_id="get_hsgt_moneyflow",
                name="🌏 北向资金",
                description="获取北向资金流向",
                category="market",
                data_source="tushare",
                timeout=30,
                icon="🌏",
                parameters=[]
            ),
            ToolDefinition(
                tool_id="get_industry_flow",
                name="🏭 行业资金流",
                description="获取行业资金流向",
                category="market",
                data_source="tushare",
                timeout=30,
                icon="🏭",
                parameters=[
                    ToolParameter("limit", "int", "返回数量，默认10", False, 10),
                ]
            ),
            ToolDefinition(
                tool_id="get_stock_news_unified",
                name="📰 统一新闻数据",
                description="获取股票相关新闻的统一接口",
                category="news",
                data_source="finnhub/google",
                timeout=30,
                icon="📰",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码", True),
                    ToolParameter("limit", "int", "返回新闻数量，默认10", False, 10),
                ]
            ),
            ToolDefinition(
                tool_id="get_stock_sentiment_unified",
                name="💬 情绪分析",
                description="获取股票社交媒体情绪的统一接口",
                category="social",
                data_source="reddit/twitter",
                timeout=30,
                icon="💬",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码", True),
                ]
            ),
            ToolDefinition(
                tool_id="get_technical_indicators",
                name="🔧 技术指标计算",
                description="计算股票技术指标（MACD、RSI、布林带等）",
                category="technical",
                data_source="internal",
                timeout=30,
                icon="🔧",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码", True),
                    ToolParameter("indicators", "string", "指标列表，如 MACD,RSI,BOLL", False, "MACD,RSI,BOLL"),
                ]
            ),
            ToolDefinition(
                tool_id="get_china_stock_data",
                name="🏠 中国A股数据",
                description="获取中国A股市场数据",
                category="china",
                data_source="akshare/tushare",
                timeout=30,
                icon="🏠",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码，如 600000", True),
                    ToolParameter("start_date", "string", "开始日期", False),
                    ToolParameter("end_date", "string", "结束日期", False),
                ]
            ),
            ToolDefinition(
                tool_id="get_hk_stock_data",
                name="🏙️ 港股数据",
                description="获取香港股票市场数据",
                category="china",
                data_source="akshare/yfinance",
                timeout=30,
                icon="🏙️",
                parameters=[
                    ToolParameter("ticker", "string", "港股代码，如 00700", True),
                    ToolParameter("start_date", "string", "开始日期", False),
                    ToolParameter("end_date", "string", "结束日期", False),
                ]
            ),
            ToolDefinition(
                name="🏛️ 美股数据",
                tool_id="get_us_stock_data",
                description="获取美国股票市场数据",
                category="market",
                data_source="yfinance/finnhub",
                timeout=30,
                icon="🏛️",
                parameters=[
                    ToolParameter("ticker", "string", "美股代码，如 AAPL", True),
                    ToolParameter("start_date", "string", "开始日期", False),
                    ToolParameter("end_date", "string", "结束日期", False),
                ]
            ),
            ToolDefinition(
                tool_id="get_company_info",
                name="🏢 公司信息",
                description="获取公司基本信息",
                category="fundamentals",
                data_source="multiple",
                timeout=30,
                icon="🏢",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码", True),
                ]
            ),
            ToolDefinition(
                tool_id="get_realtime_news",
                name="📢 实时新闻",
                description="获取实时新闻数据",
                category="news",
                data_source="google news",
                timeout=30,
                icon="📢",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码或关键词", True),
                    ToolParameter("limit", "int", "返回数量，默认5", False, 5),
                ]
            ),
            ToolDefinition(
                tool_id="get_trade_records",
                name="📋 交易记录",
                description="从数据库获取交易记录",
                category="replay",
                data_source="database",
                timeout=30,
                icon="📋",
                parameters=[
                    ToolParameter("ticker", "string", "股票代码（可选）", False),
                    ToolParameter("start_date", "string", "开始日期（可选）", False),
                    ToolParameter("end_date", "string", "结束日期（可选）", False),
                ]
            ),
            ToolDefinition(
                tool_id="build_trade_info",
                name="🔨 构建交易信息",
                description="从交易记录构建完整的交易信息对象",
                category="replay",
                data_source="internal",
                timeout=30,
                icon="🔨",
                parameters=[
                    ToolParameter("trade_id", "string", "交易记录ID", True),
                ]
            ),
        ]
        
        for tool in default_tools:
            self.register_tool(tool)
            self._enabled_tools.add(tool.tool_id)
        
        # 注册 provider_tools 中的所有工具
        self._register_provider_tools()
    
    def _register_provider_tools(self):
        """注册 provider_tools 中的所有工具"""
        try:
            from app.services.llm.tools.provider_tools import PROVIDER_TOOLS
            from app.services.llm.tools.akshare_tools import AKSHARE_TOOLS
            from app.services.llm.tools.baostock_tools import BAOSTOCK_TOOLS
            
            all_provider_tools = []
            
            # Juhe tools - from provider_tools
            juhe_tool_names = ['get_stock_quote_juhe', 'get_stock_daily_juhe']
            for tool in PROVIDER_TOOLS:
                tool_name = tool.name
                if tool_name in juhe_tool_names:
                    source = 'juhe'
                elif 'tushare' in tool_name.lower():
                    source = 'tushare'
                elif 'akshare' in tool_name.lower():
                    source = 'akshare'
                elif 'baostock' in tool_name.lower():
                    source = 'baostock'
                else:
                    source = 'other'
                tool_def = self._convert_langchain_tool(tool, source)
                all_provider_tools.append(tool_def)
                # 注册工具函数
                self._tool_functions[tool_name] = tool
            
            # AKShare tools
            for tool in AKSHARE_TOOLS:
                tool_def = self._convert_langchain_tool(tool, 'akshare')
                all_provider_tools.append(tool_def)
                self._tool_functions[tool.name] = tool
            
            # BaoStock tools
            for tool in BAOSTOCK_TOOLS:
                tool_def = self._convert_langchain_tool(tool, 'baostock')
                all_provider_tools.append(tool_def)
                self._tool_functions[tool.name] = tool
            
            # 注册所有工具 - 但不要自动添加到启用列表
            # 启用列表应该从数据库加载，不要覆盖
            for tool in all_provider_tools:
                self._tools[tool.tool_id] = tool
                    
            logger.info(f"Registered {len(all_provider_tools)} provider tools, {len(self._tool_functions)} functions")
            
        except ImportError as e:
            logger.warning(f"Could not import provider tools: {e}")
        except Exception as e:
            logger.error(f"Error registering provider tools: {e}")
    
    def _convert_langchain_tool(self, langchain_tool, data_source: str) -> ToolDefinition:
        """将 LangChain tool 转换为 ToolDefinition"""
        # 获取工具名称和描述
        tool_name = langchain_tool.name
        tool_desc = langchain_tool.description or ""
        
        # 提取参数
        parameters = []
        if hasattr(langchain_tool, 'args_schema') and langchain_tool.args_schema:
            try:
                schema = langchain_tool.args_schema.model_json_schema() if hasattr(langchain_tool.args_schema, 'model_json_schema') else {}
                props = schema.get('properties', {})
                required = schema.get('required', [])
                for param_name, param_info in props.items():
                    parameters.append(ToolParameter(
                        name=param_name,
                        type=param_info.get('type', 'string'),
                        description=param_info.get('description', ''),
                        required=param_name in required
                    ))
            except Exception:
                pass
        
        # 根据工具名推断图标
        icon = "📊"
        if 'quote' in tool_name.lower() or '行情' in tool_desc:
            icon = "📈"
        elif 'daily' in tool_name.lower() or '日线' in tool_desc:
            icon = "📊"
        elif 'financial' in tool_name.lower() or '财务' in tool_desc:
            icon = "💰"
        elif 'fund_flow' in tool_name.lower() or '资金' in tool_desc:
            icon = "💵"
        elif 'margin' in tool_name.lower() or '融资' in tool_desc:
            icon = "💳"
        
        return ToolDefinition(
            tool_id=tool_name,
            name=f"{icon} {tool_name}",
            description=tool_desc[:200] if tool_desc else tool_name,
            category=data_source,  # 使用数据源作为分类
            data_source=data_source,
            timeout=30,
            icon=icon,
            parameters=parameters,
            is_enabled=True
        )
    
    def register_tool(self, tool: ToolDefinition):
        """注册工具"""
        self._tools[tool.tool_id] = tool
        logger.info(f"Registered tool: {tool.tool_id} - {tool.name}")
    
    def register_tool_function(self, tool_id: str, func: Any):
        """注册工具函数"""
        self._tool_functions[tool_id] = func
    
    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self._tools.get(tool_id)
    
    def get_all_tools(self) -> List[ToolDefinition]:
        """获取所有工具"""
        return list(self._tools.values())
    
    def get_enabled_tools(self) -> List[ToolDefinition]:
        """获取所有启用的工具"""
        return [t for t in self._tools.values() if t.is_enabled]
    
    def get_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """按分类获取工具"""
        return [t for t in self._tools.values() if t.category == category]
    
    def get_tool_function(self, tool_id: str) -> Optional[Any]:
        """获取工具函数"""
        return self._tool_functions.get(tool_id)
    
    def get_enabled_tool_functions(self) -> List[Any]:
        """获取所有启用的工具函数（LangChain工具）"""
        enabled = []
        for tool_id in self._enabled_tools:
            func = self._tool_functions.get(tool_id)
            if func:
                enabled.append(func)
        return enabled
    
    def set_tool_enabled(self, tool_id: str, enabled: bool):
        """设置工具启用状态"""
        if tool_id in self._tools:
            self._tools[tool_id].is_enabled = enabled
            if enabled:
                self._enabled_tools.add(tool_id)
            else:
                self._enabled_tools.discard(tool_id)
            logger.info(f"Tool {tool_id} enabled={enabled}")
            
            # 保存到数据库
            self._save_enabled_tools_to_db(list(self._enabled_tools))
    
    def is_tool_enabled(self, tool_id: str) -> bool:
        """检查工具是否启用"""
        return tool_id in self._enabled_tools
    
    def get_enabled_tool_ids(self) -> List[str]:
        """获取启用的工具ID列表"""
        return list(self._enabled_tools)
    
    def set_enabled_tool_ids(self, tool_ids: List[str]):
        """设置启用的工具ID列表，保存到数据库"""
        self._enabled_tools = set(tool_ids)
        for tool_id, tool in self._tools.items():
            tool.is_enabled = tool_id in self._enabled_tools
        logger.info(f"Enabled tools updated: {tool_ids}")
        
        # 保存到数据库
        self._save_enabled_tools_to_db(tool_ids)
    
    def _save_enabled_tools_to_db(self, tool_ids: List[str]):
        """保存启用工具到数据库"""
        try:
            from app.database.session import get_db
            from app.models.config import ToolConfig
            
            db = next(get_db())
            
            # 删除旧的配置
            db.query(ToolConfig).delete()
            
            # 插入新的配置
            for tool_id in tool_ids:
                config = ToolConfig(tool_id=tool_id, is_enabled=True)
                db.add(config)
            
            db.commit()
            logger.info(f"Saved {len(tool_ids)} enabled tools to database")
        except Exception as e:
            logger.error(f"Failed to save enabled tools to database: {e}")
    
    def _load_enabled_tools_from_db(self) -> List[str]:
        """从数据库加载启用工具"""
        try:
            from app.database.session import get_db
            from app.models.config import ToolConfig
            
            db = next(get_db())
            enabled = db.query(ToolConfig).filter(ToolConfig.is_enabled == True).all()
            return [t.tool_id for t in enabled]
        except Exception as e:
            logger.warning(f"Failed to load enabled tools from database: {e}")
            return []
    
    def get_all_categories(self) -> List[ToolCategory]:
        """获取所有分类"""
        return list(self._categories.values())
    
    def get_category(self, category_id: str) -> Optional[ToolCategory]:
        """获取分类"""
        return self._categories.get(category_id)
    
    def register_category(self, category: ToolCategory):
        """注册分类"""
        self._categories[category.id] = category
    
    def refresh_tools(self):
        """刷新工具列表"""
        self._tool_functions.clear()
        
        try:
            from app.services.llm.tools import PROVIDER_TOOLS, STOCK_TOOLS
            
            tools_to_register = PROVIDER_TOOLS if PROVIDER_TOOLS else STOCK_TOOLS
            
            for tool in tools_to_register:
                tool_id = tool.name.replace("get_", "")
                
                provider_name = ""
                data_type = tool_id
                
                if "_" in tool_id:
                    parts = tool_id.rsplit("_", 1)
                    data_type = parts[0]
                    provider_name = parts[1] if len(parts) > 1 else ""
                
                tool_def = ToolDefinition(
                    tool_id=tool_id,
                    name=tool.name,
                    description=tool.description or f"获取{data_type}数据",
                    category="provider",
                    data_source=provider_name,
                    timeout=30,
                    icon="📊",
                    parameters=[]
                )
                
                self.register_tool(tool_def)
                self.register_tool_function(tool_id, tool)
            
            logger.info(f"Refreshed {len(tools_to_register)} provider tools")
        except Exception as e:
            logger.error(f"Error refreshing tools: {e}")
        
        logger.info("Tools refreshed")


_registry_instance: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """获取工具注册表实例（单例）"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance


def get_all_tools_json() -> List[dict]:
    """获取所有工具JSON格式"""
    registry = get_registry()
    tools = registry.get_all_tools()
    return [t.to_dict() for t in tools]


def get_enabled_tools_json() -> List[dict]:
    """获取启用的工具JSON格式"""
    registry = get_registry()
    tools = registry.get_enabled_tools()
    return [t.to_dict() for t in tools]
