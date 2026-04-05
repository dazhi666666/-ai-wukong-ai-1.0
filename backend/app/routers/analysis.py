"""
股票分析 API 路由
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analysis.workflow import get_or_create_analysis_conversations, get_stock_data_for_analysis
from app.services.analysis.agents import get_all_agents
from app.services.analysis.stock_analysis_service import StockAnalysisService, analyze_stock as analyze_stock_with_agents
from app.services.agent.agent_service import AgentService
from app.services.logging_manager import get_logger

logger = get_logger("analysis_router")

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class StockAnalysisRequest(BaseModel):
    symbol: str
    provider: str = "juhe"


class StockAnalysisResponse(BaseModel):
    symbol: str
    fundamental_conv_id: str
    technical_conv_id: str
    risk_conv_id: str
    decision_conv_id: str
    is_new: bool
    stock_data: Optional[dict] = None


@router.post("/stock", response_model=StockAnalysisResponse)
async def analyze_stock(
    request: StockAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    准备股票分析 - 创建/获取对话ID
    
    前端获取对话ID后，自行调用 /api/chat/stream 发送消息
    这样可以复用现有的流式输出功能
    """
    if not request.symbol:
        raise HTTPException(status_code=400, detail="股票代码不能为空")
    
    # 清理股票代码
    symbol = request.symbol.strip().upper()
    
    logger.info(f"Preparing analysis for {symbol}")
    
    try:
        # 1. 获取或创建4个对话
        conv_ids = await get_or_create_analysis_conversations(symbol, db)
        is_new = bool(conv_ids.pop("is_new"))
        
        # 2. 预获取股票数据 (用于前端构建prompt)
        stock_data = await get_stock_data_for_analysis(symbol, request.provider)
        
        return StockAnalysisResponse(
            symbol=symbol,
            fundamental_conv_id=conv_ids["fundamental"],
            technical_conv_id=conv_ids["technical"],
            risk_conv_id=conv_ids["risk"],
            decision_conv_id=conv_ids["decision"],
            is_new=is_new,
            stock_data=stock_data
        )
        
    except Exception as e:
        logger.error(f"Analysis prep failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents():
    """获取所有可用的智能体"""
    agents = get_all_agents()
    
    result = []
    for key, agent in agents.items():
        result.append({
            "id": key,
            "name": agent["name"],
            "title": agent["title"],
            "description": agent["description"],
            "temperature": agent["temperature"],
            "data_types": agent["data_types"],
            "system_prompt": agent["system_prompt"]
        })
    
    return {"agents": result}


@router.get("/status/{symbol}")
async def get_analysis_status(
    symbol: str,
    db: Session = Depends(get_db)
):
    """检查某股票是否已有分析对话"""
    from app.models import Conversation
    
    symbol = symbol.strip().upper()
    
    # 查询相关对话
    conversations = db.query(Conversation).filter(
        Conversation.title.like(f"%-{symbol}")
    ).all()
    
    result = {
        "symbol": symbol,
        "has_analysis": len(conversations) > 0,
        "conversations": {}
    }
    
    for conv in conversations:
        title = conv.title
        if "基本面" in title:
            result["conversations"]["fundamental"] = conv.id
        elif "技术" in title:
            result["conversations"]["technical"] = conv.id
        elif "风控" in title:
            result["conversations"]["risk"] = conv.id
        elif "决策" in title:
            result["conversations"]["decision"] = conv.id
    
    return result


@router.get("/conversation/{conv_id}/last-ai-message")
async def get_last_ai_message(
    conv_id: str,
    db: Session = Depends(get_db)
):
    """获取对话中最后一条AI回复"""
    from app.models import Message
    
    messages = db.query(Message).filter(
        Message.conversation_id == conv_id,
        Message.role == "assistant"
    ).order_by(Message.timestamp.desc()).all()
    
    if messages and messages[0].timestamp:
        return {
            "content": messages[0].content,
            "timestamp": messages[0].timestamp.isoformat()
        }
    
    return {"content": None}


# ============================================================
# 新API端点：使用Agent配置管理系统的分析接口
# ============================================================

class StockAnalysisV2Request(BaseModel):
    """股票分析V2请求（使用Agent配置系统）"""
    symbol: str
    analysis_types: Optional[List[str]] = None  # 默认为 ['fundamental', 'technical', 'risk', 'decision']
    prompt_version: Optional[str] = None  # 提示词版本：'conservative', 'neutral', 'aggressive'，默认None使用Agent配置的默认版本
    context: Optional[Dict[str, Any]] = None  # 额外的上下文信息


class StockAnalysisV2Response(BaseModel):
    """股票分析V2响应"""
    symbol: str
    analysis_date: str
    prompt_version: str
    status: str
    stock_info: Optional[Dict[str, Any]] = None
    stages: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/stock/v2", response_model=StockAnalysisV2Response)
async def analyze_stock_v2(
    request: StockAnalysisV2Request,
    db: Session = Depends(get_db)
):
    """
    股票分析V2 - 使用Agent配置管理系统
    
    此端点与Agent配置系统集成，支持：
    - 使用数据库中配置的Agent进行分析
    - 支持多版本提示词（保守/中性/激进）
    - 4阶段分析流程：基本面/技术并行 → 风控 → 决策
    
    Args:
        symbol: 股票代码
        analysis_types: 分析类型列表，可选
        prompt_version: 提示词版本，可选（'conservative', 'neutral', 'aggressive'）
        context: 额外的上下文信息
        
    Returns:
        分析结果，包含各阶段的详细输出
    """
    if not request.symbol:
        raise HTTPException(status_code=400, detail="股票代码不能为空")
    
    # 清理股票代码
    symbol = request.symbol.strip().upper()
    
    logger.info(f"Starting stock analysis v2 for {symbol}")
    logger.info(f"Analysis types: {request.analysis_types}")
    logger.info(f"Prompt version: {request.prompt_version}")
    
    try:
        # 创建分析服务
        analysis_service = StockAnalysisService(db)
        
        # 执行分析
        result = await analysis_service.analyze(
            symbol=symbol,
            analysis_types=request.analysis_types,
            context=request.context or {},
            prompt_version=request.prompt_version
        )
        
        logger.info(f"Stock analysis v2 completed for {symbol}")
        
        return StockAnalysisV2Response(
            symbol=result["symbol"],
            analysis_date=result["analysis_date"],
            prompt_version=result.get("prompt_version", "default"),
            status="completed",
            stock_info=result.get("stock_info"),
            stages=result.get("stages")
        )
        
    except Exception as e:
        logger.error(f"Stock analysis v2 failed for {symbol}: {e}")
        return StockAnalysisV2Response(
            symbol=symbol,
            analysis_date=datetime.now().isoformat(),
            prompt_version=request.prompt_version or "default",
            status="failed",
            error=str(e)
        )


@router.get("/stock/v2/agents")
async def list_analysis_agents(db: Session = Depends(get_db)):
    """
    获取股票分析可用的Agent列表
    
    返回当前Agent配置管理系统中用于股票分析的Agent
    """
    agent_service = AgentService(db)
    
    # 股票分析相关的Agent slug
    analysis_slugs = [
        "fundamentals_analyst_v2",
        "market_analyst_v2", 
        "neutral_debator",
        "research_manager"
    ]
    
    agents = []
    for slug in analysis_slugs:
        agent = agent_service.get_agent_by_slug(slug)
        if agent:
            agents.append(agent_service.to_dict(agent, include_prompts=False, include_config=True))
    
    return {
        "agents": agents,
        "analysis_types": {
            "fundamental": "fundamentals_analyst_v2",
            "technical": "market_analyst_v2",
            "risk": "neutral_debator", 
            "decision": "research_manager"
        }
    }


@router.get("/stock/v2/{symbol}/status")
async def get_analysis_v2_status(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    获取股票分析V2的状态
    
    检查某股票是否已有完成的分析，以及各Agent的执行情况
    """
    # 使用现有的状态检查逻辑
    from app.models import Conversation
    
    symbol = symbol.strip().upper()
    
    # 查询相关对话
    conversations = db.query(Conversation).filter(
        Conversation.title.like(f"%-{symbol}")
    ).all()
    
    result = {
        "symbol": symbol,
        "has_analysis": len(conversations) > 0,
        "conversations": {},
        "agent_status": {}
    }
    
    # 使用Agent配置系统的映射
    agent_mapping = {
        "基本面": "fundamentals_analyst_v2",
        "技术": "market_analyst_v2",
        "风控": "neutral_debator",
        "决策": "research_manager"
    }
    
    for conv in conversations:
        title = conv.title
        for keyword, agent_slug in agent_mapping.items():
            if keyword in title:
                result["conversations"][keyword] = {
                    "conversation_id": conv.id,
                    "agent_slug": agent_slug,
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
                }
    
    return result
