"""
股票分析服务 - 集成Agent配置系统
支持基本面、技术面、风控、决策四个阶段的分析
使用混合数据流：简单数据由工作流传递，复杂数据让Agent通过工具获取
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models import Conversation, Message
from app.services.agent.executor import AgentExecutor
from app.services.agent.agent_service import AgentService
from app.services.logging_manager import get_logger

logger = get_logger("stock_analysis_service")


class StockAnalysisService:
    """股票分析服务，集成Agent配置管理系统"""
    
    # Agent slug映射 - 将分析类型映射到Agent配置系统中的Agent
    AGENT_SLUGS = {
        "fundamental": "fundamentals_analyst_v2",  # 基本面分析师
        "technical": "market_analyst_v2",            # 市场分析师（技术分析）
        "risk": "neutral_debator",                   # 中性分析师（风险评估）
        "decision": "research_manager"             # 研究经理（投资决策）
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_service = AgentService(db)
        self.agent_executor = AgentExecutor(db)
    
    async def analyze(
        self, 
        symbol: str,
        analysis_types: List[str] = None,
        context: Dict[str, Any] = None,
        prompt_version: str = None  # 默认使用Agent配置的默认版本
    ) -> Dict[str, Any]:
        """
        执行股票分析
        
        Args:
            symbol: 股票代码
            analysis_types: 分析类型列表 ['fundamental', 'technical', 'risk', 'decision']
            context: 额外的上下文信息
            prompt_version: 提示词版本（'conservative', 'neutral', 'aggressive'），默认None使用Agent配置的默认版本
            
        Returns:
            分析结果字典
        """
        if analysis_types is None:
            analysis_types = ['fundamental', 'technical', 'risk', 'decision']
        
        if context is None:
            context = {}
        
        # 获取股票基本信息（简单数据直接传递）
        stock_info = await self._get_stock_info(symbol)
        
        results = {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "stock_info": stock_info,
            "prompt_version": prompt_version or "default",
            "stages": {}
        }
        
        # 阶段1：基本面分析和技术分析（并行）
        if 'fundamental' in analysis_types or 'technical' in analysis_types:
            logger.info(f"开始阶段1分析: {symbol}")
            stage1_results = await self._run_stage1(
                symbol, stock_info, analysis_types, context, prompt_version
            )
            results["stages"]["stage1"] = stage1_results
            
            # 将阶段1结果传递到上下文
            if 'fundamental' in stage1_results:
                context['fundamental_analysis'] = stage1_results['fundamental'].get('result', '')
            if 'technical' in stage1_results:
                context['technical_analysis'] = stage1_results['technical'].get('result', '')
        
        # 阶段2：风控分析
        if 'risk' in analysis_types:
            logger.info(f"开始风控分析: {symbol}")
            risk_result = await self._run_risk_analysis(symbol, stock_info, context, prompt_version)
            results["stages"]["risk"] = risk_result
            context['risk_analysis'] = risk_result.get('result', '')
        
        # 阶段3：决策分析
        if 'decision' in analysis_types:
            logger.info(f"开始决策分析: {symbol}")
            decision_result = await self._run_decision_analysis(symbol, stock_info, context, prompt_version)
            results["stages"]["decision"] = decision_result
        
        return results
    
    async def _get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息（简单数据，直接返回避免依赖外部服务）"""
        return {
            "symbol": symbol,
            "name": symbol,
            "market": "A股",
            "currency": "人民币"
        }
    
    async def _run_stage1(
        self, 
        symbol: str, 
        stock_info: Dict[str, Any],
        analysis_types: List[str],
        context: Dict[str, Any],
        prompt_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行阶段1：基本面分析和技术分析（并行）"""
        tasks = []
        task_types = []
        
        if 'fundamental' in analysis_types:
            tasks.append(self._run_agent(
                'fundamental', symbol, stock_info, context, prompt_version
            ))
            task_types.append('fundamental')
        
        if 'technical' in analysis_types:
            tasks.append(self._run_agent(
                'technical', symbol, stock_info, context, prompt_version
            ))
            task_types.append('technical')
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for i, (task_type, result) in enumerate(zip(task_types, results)):
            if isinstance(result, Exception):
                logger.error(f"{task_type} analysis failed: {result}")
                output[task_type] = {
                    "success": False,
                    "error": str(result),
                    "agent_type": task_type
                }
            else:
                output[task_type] = result
        
        return output
    
    async def _run_agent(
        self, 
        agent_type: str, 
        symbol: str, 
        stock_info: Dict[str, Any],
        context: Dict[str, Any],
        prompt_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """运行指定的Agent"""
        agent_slug = self.AGENT_SLUGS.get(agent_type)
        if not agent_slug:
            return {
                "success": False,
                "error": f"未知的Agent类型: {agent_type}",
                "agent_type": agent_type
            }
        
        agent = self.agent_service.get_agent_by_slug(agent_slug)
        if not agent:
            return {
                "success": False,
                "error": f"Agent不存在: {agent_slug}",
                "agent_type": agent_type
            }
        
        # 获取或创建分析对话
        conversation = await self._get_or_create_conversation(symbol, agent_type)
        if not conversation:
            logger.warning(f"Could not get/create conversation for {agent_type}-{symbol}")
        
        # 准备输入参数（简单数据直接传递）
        inputs = {
            "ticker": symbol,
            "company_name": stock_info.get("name", symbol),
            "market_name": stock_info.get("market", "A股"),
            "currency_name": stock_info.get("currency", "人民币"),
            "currency_symbol": "¥",
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        # 添加上下文信息（如果有）
        if 'fundamental_analysis' in context:
            inputs['fundamental_analysis'] = context['fundamental_analysis']
        if 'technical_analysis' in context:
            inputs['technical_analysis'] = context['technical_analysis']
        if 'risk_analysis' in context:
            inputs['risk_analysis'] = context['risk_analysis']
        
        # 构建用户消息（用于保存）
        user_message_content = self._build_user_message(agent_type, symbol, inputs, context)
        
        try:
            # 保存用户消息到对话
            if conversation:
                await self._save_message(conversation.id, "user", user_message_content)
            
            # 使用AgentExecutor执行Agent
            result = await self.agent_executor.execute(
                agent_id=agent.id,
                inputs=inputs,
                prompt_version=prompt_version
            )
            
            # 保存AI回复到对话
            if conversation and result.get("success"):
                await self._save_message(
                    conversation.id, 
                    "assistant", 
                    result.get("result", "")
                )
            
            # 添加Agent信息到结果
            result['agent_type'] = agent_type
            result['agent_name'] = agent.name
            result['agent_slug'] = agent_slug
            result['success'] = result.get('success', True)
            result['conversation_id'] = conversation.id if conversation else None
            
            return result
            
        except Exception as e:
            logger.error(f"Agent execution failed for {agent_type}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": agent_type,
                "agent_name": agent.name if agent else agent_slug
            }
    
    async def _get_or_create_conversation(self, symbol: str, agent_type: str) -> Optional[Conversation]:
        """获取或创建分析对话"""
        # 对话名称映射
        agent_names = {
            "fundamental": "基本面分析",
            "technical": "技术分析",
            "risk": "风控分析",
            "decision": "决策分析"
        }
        
        title_prefix = f"{agent_names.get(agent_type, agent_type)}-{symbol}"
        
        # 使用 symbol + agent_type 精确查询
        existing = self.db.query(Conversation).filter(
            Conversation.symbol == symbol,
            Conversation.agent_type == agent_type
        ).first()
        
        if existing:
            # 更新标题以保持一致
            if existing.title != title_prefix:
                existing.title = title_prefix
                self.db.commit()
            return existing
        
        # 创建新对话
        conv_id = str(uuid4())[:8]
        conversation = Conversation(
            id=conv_id,
            title=title_prefix,
            symbol=symbol,
            agent_type=agent_type
        )
        self.db.add(conversation)
        self.db.commit()
        logger.info(f"Created analysis conversation: {title_prefix} -> {conv_id}")
        return conversation
    
    def _build_user_message(
        self, 
        agent_type: str, 
        symbol: str, 
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """构建用户消息内容"""
        agent_names = {
            "fundamental": "基本面分析师",
            "technical": "技术分析师",
            "risk": "风险分析师",
            "decision": "投资决策经理"
        }
        
        messages = {
            "fundamental": f"请作为{agent_names.get(agent_type)}分析股票 {symbol} 的基本面情况。\n\n股票信息：{inputs.get('company_name', symbol)}",
            "technical": f"请作为{agent_names.get(agent_type)}分析股票 {symbol} 的技术面情况。\n\n股票信息：{inputs.get('company_name', symbol)}",
            "risk": f"请作为{agent_names.get(agent_type)}对股票 {symbol} 进行风险评估。",
            "decision": f"请作为{agent_names.get(agent_type)}给出股票 {symbol} 的投资决策建议。"
        }
        
        content = messages.get(agent_type, f"请分析股票 {symbol}")
        
        # 添加上下文信息
        if agent_type == "risk" and context:
            if 'fundamental_analysis' in context:
                content += f"\n\n【基本面分析】\n{context['fundamental_analysis']}"
            if 'technical_analysis' in context:
                content += f"\n\n【技术分析】\n{context['technical_analysis']}"
        elif agent_type == "decision" and context:
            if 'fundamental_analysis' in context:
                content += f"\n\n【基本面分析】\n{context['fundamental_analysis']}"
            if 'technical_analysis' in context:
                content += f"\n\n【技术分析】\n{context['technical_analysis']}"
            if 'risk_analysis' in context:
                content += f"\n\n【风险分析】\n{context['risk_analysis']}"
        
        return content
    
    async def _save_message(self, conversation_id: str, role: str, content: str):
        """保存消息到数据库"""
        try:
            message = Message(
                id=str(uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content
            )
            self.db.add(message)
            self.db.commit()
            logger.info(f"Saved {role} message to conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            self.db.rollback()
    
    async def _run_risk_analysis(
        self, 
        symbol: str, 
        stock_info: Dict[str, Any],
        context: Dict[str, Any],
        prompt_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行风控分析"""
        return await self._run_agent('risk', symbol, stock_info, context, prompt_version)
    
    async def _run_decision_analysis(
        self, 
        symbol: str, 
        stock_info: Dict[str, Any],
        context: Dict[str, Any],
        prompt_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行决策分析"""
        return await self._run_agent('decision', symbol, stock_info, context, prompt_version)


# 便捷函数
async def analyze_stock(
    db: Session,
    symbol: str,
    analysis_types: List[str] = None,
    context: Dict[str, Any] = None,
    prompt_version: str = None
) -> Dict[str, Any]:
    """
    便捷函数：分析股票
    
    使用示例:
        result = await analyze_stock(db, "000001", ["fundamental", "technical"])
    """
    service = StockAnalysisService(db)
    return await service.analyze(symbol, analysis_types, context, prompt_version)