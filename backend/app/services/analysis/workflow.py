"""
股票分析工作流
管理多智能体分析流程和对话
与Agent配置管理系统集成
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from app.models import Conversation, Message
from app.services.llm.chat_service import ChatService
from app.services.config_service import ConfigService
from app.services.llm.factory import get_provider_for_model
from .agents import AGENTS, get_agent_by_name
from .data_fetcher import StockDataFetcher
from .stock_analysis_service import StockAnalysisService, analyze_stock as analyze_stock_service
from app.services.logging_manager import get_logger

logger = get_logger("analysis.workflow")

# 对话名称前缀
CONVERSATION_PREFIX = "分析"

# 智能体顺序
AGENT_ORDER = ["fundamental", "technical", "risk", "decision"]


async def get_or_create_analysis_conversations(
    symbol: str, 
    db: Session
) -> Dict[str, str]:
    """
    获取或创建某股票的4个分析对话
    
    Returns:
        {
            "fundamental": "conv_id",
            "technical": "conv_id",
            "risk": "conv_id", 
            "decision": "conv_id",
            "is_new": True/False
        }
    """
    conv_ids = {}
    is_new = False
    
    # 对话名称映射
    agent_names = {
        "fundamental": "基本面分析",
        "technical": "技术分析",
        "risk": "风控分析",
        "decision": "决策分析"
    }
    
    is_new = False
    
    for agent_key in AGENT_ORDER:
        title_prefix = f"{agent_names[agent_key]}-{symbol}"
        
        # 使用 symbol + agent_type 精确查询
        existing = db.query(Conversation).filter(
            Conversation.symbol == symbol,
            Conversation.agent_type == agent_key
        ).first()
        
        if existing:
            conv_ids[agent_key] = existing.id
            # 更新标题以保持一致
            if existing.title != title_prefix:
                existing.title = title_prefix
                db.commit()
            logger.info(f"Found existing conversation: {agent_key}-{symbol} -> {existing.id}")
        else:
            # 创建新对话
            conv_id = str(uuid4())[:8]
            conversation = Conversation(
                id=conv_id,
                title=title_prefix,
                symbol=symbol,
                agent_type=agent_key
            )
            db.add(conversation)
            db.commit()
            conv_ids[conv_id] = conv_id
            is_new = True
            logger.info(f"Created new conversation: {title_prefix} -> {conv_id}")
    
    conv_ids["is_new"] = is_new
    return conv_ids


async def send_message_to_conversation(
    conversation_id: str,
    prompt: str,
    db: Session,
    provider: str = "deepseek",
    model: str = "deepseek-chat",
    temperature: float = 0.7
) -> str:
    """
    发送消息到对话并获取响应
    
    Returns:
        模型响应内容
    """
    # 获取对话
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        logger.error(f"Conversation not found: {conversation_id}")
        return "错误：对话不存在"
    
    # 获取记忆模式配置
    config_service = ConfigService(db)
    config = config_service.get_config_by_provider_model(provider, model)
    memory_mode = "enhanced"  # 默认使用增强模式
    if config and hasattr(config, 'enable_memory'):
        memory_mode = str(config.enable_memory) if config.enable_memory else "enhanced"
    
    # 使用 ChatService 发送消息
    chat_service = ChatService(db)
    
    try:
        result = await chat_service.chat(
            prompt=prompt,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            temperature=temperature,
            memory_mode=memory_mode
        )
        
        response = result.get("response", "无响应")
        logger.info(f"Chat response for conversation {conversation_id}: {response[:100]}...")
        return response
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return f"错误：{str(e)}"


async def run_stock_analysis(
    symbol: str,
    db: Session,
    provider: str = "juhe"
) -> Dict[str, Any]:
    """
    运行股票分析工作流 - 与Agent配置管理系统集成版本
    
    流程：
    1. 获取或创建4个分析对话
    2. 使用StockAnalysisService执行分析
    3. 保留4阶段流程：基本面/技术并行 → 风控 → 决策
    
    Returns:
        {
            "fundamental_conv_id": "xxx",
            "technical_conv_id": "xxx",
            "risk_conv_id": "xxx",
            "decision_conv_id": "xxx",
            "symbol": symbol,
            "is_new": True/False,
            "status": "completed",
            "stages": {...}  # 各阶段详细结果
        }
    """
    logger.info(f"=== Starting stock analysis (Agent Config System) for {symbol} ===")
    
    # Step 1: 获取或创建对话
    conv_ids = await get_or_create_analysis_conversations(symbol, db)
    is_new = conv_ids.pop("is_new")
    
    # Step 2: 使用新的StockAnalysisService执行分析
    logger.info(f"Running analysis using Agent Config System...")
    
    try:
        # 使用便捷函数直接调用服务
        analysis_result = await analyze_stock_service(
            db=db,
            symbol=symbol,
            analysis_types=['fundamental', 'technical', 'risk', 'decision']
        )
        
        logger.info(f"Analysis completed for {symbol}")
        
        # 合并结果
        return {
            "fundamental_conv_id": conv_ids["fundamental"],
            "technical_conv_id": conv_ids["technical"],
            "risk_conv_id": conv_ids["risk"],
            "decision_conv_id": conv_ids["decision"],
            "symbol": symbol,
            "is_new": is_new,
            "status": "completed",
            "stages": analysis_result.get("stages", {}),
            "stock_info": analysis_result.get("stock_info", {}),
            "analysis_date": analysis_result.get("analysis_date", datetime.now().isoformat())
        }
        
    except Exception as e:
        logger.error(f"Analysis failed for {symbol}: {e}")
        return {
            "fundamental_conv_id": conv_ids["fundamental"],
            "technical_conv_id": conv_ids["technical"],
            "risk_conv_id": conv_ids["risk"],
            "decision_conv_id": conv_ids["decision"],
            "symbol": symbol,
            "is_new": is_new,
            "status": "failed",
            "error": str(e)
        }


async def run_stock_analysis_streaming(
    symbol: str,
    db: Session,
    provider: str = "juhe"
) -> Dict[str, Any]:
    """
    运行股票分析工作流 (流式版本)
    
    与Agent配置管理系统集成
    """
    # 复用非流式版本
    return await run_stock_analysis(symbol, db, provider)


async def get_stock_data_for_analysis(symbol: str, provider: str = "juhe") -> Dict[str, Any]:
    """
    获取股票数据供分析使用
    
    Returns:
        格式化后的股票数据
    """
    data_fetcher = StockDataFetcher(provider)
    stock_data = await data_fetcher.fetch_all_data(symbol)
    
    # 格式化各智能体需要的数据
    return {
        "fundamental": data_fetcher.format_for_agent("fundamental", stock_data),
        "technical": data_fetcher.format_for_agent("technical", stock_data),
        "risk": data_fetcher.format_for_agent("risk", stock_data),
        "raw": stock_data
    }