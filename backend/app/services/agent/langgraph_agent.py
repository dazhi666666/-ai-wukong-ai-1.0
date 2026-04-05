import logging
from typing import TypedDict, Annotated, Sequence, List, Any, cast
from langgraph.graph import StateGraph, END, START, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from app.services.logging_manager import get_logger

logger = get_logger("llm_chat.langgraph_agent")

MAX_TOOL_CALLS_DEFAULT = 20
DOOM_LOOP_THRESHOLD = 3


class AgentState(TypedDict, total=False):
    """LangGraph Agent 状态定义"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    stock_query: str
    tool_call_count: int
    final_result: str
    conversation_id: str
    reasoning: str
    doom_loop_detected: bool


def _extract_tool_names(message: BaseMessage) -> List[str]:
    """从消息中提取工具名称列表"""
    tool_calls = _get_tool_calls(message)
    return [tc.get('name', '') for tc in tool_calls]


def _check_doom_loop(messages: Sequence[BaseMessage]) -> bool:
    """检查是否检测到 doom loop（连续相同工具调用）"""
    if len(messages) < 2:
        return False
    
    last_tools = _extract_tool_names(messages[-1])
    prev_tools = _extract_tool_names(messages[-2])
    
    return bool(last_tools and prev_tools and last_tools == prev_tools)


def _extract_reasoning(messages: Sequence[BaseMessage]) -> str:
    """从消息中提取 reasoning 内容"""
    ai_messages = [m for m in messages if isinstance(m, AIMessage) and m.content]
    for msg in reversed(ai_messages):
        if hasattr(msg, 'additional_kwargs'):
            reasoning = msg.additional_kwargs.get('reasoning_content', '')
            if reasoning:
                return reasoning
    return ""


def _get_tool_calls(message: BaseMessage) -> List[Any]:
    """安全获取消息的工具调用列表"""
    try:
        msg_any: Any = message
        if hasattr(msg_any, 'tool_calls') and msg_any.tool_calls:
            return msg_any.tool_calls
    except (AttributeError, TypeError):
        pass
    return []


def create_tool_node(tools: List[BaseTool]) -> ToolNode:
    """创建工具执行节点"""
    return ToolNode(tools)


def create_agent_node(
    llm: BaseChatModel,
    tools: List[BaseTool],
    system_prompt: str
):
    """创建 Agent 节点 (LLM + 工具绑定)"""
    llm_with_tools = llm.bind_tools(tools)
    
    def agent_node(state: AgentState) -> AgentState:
        messages = state.get("messages", [])
        
        system_msg = SystemMessage(content=system_prompt)
        
        has_system = any(isinstance(m, SystemMessage) for m in messages)
        full_messages = list(messages) if has_system else [system_msg] + list(messages)
        
        logger.info(f"[Agent Node] 调用LLM，当前消息数: {len(full_messages)}")
        
        response = llm_with_tools.invoke(full_messages)
        
        tool_count = state.get("tool_call_count", 0)
        tool_calls = _get_tool_calls(response)
        if tool_calls:
            tool_count += len(tool_calls)
            logger.info(f"[Agent Node] 检测到 {len(tool_calls)} 个工具调用")
        
        reasoning = ""
        response_any = cast(Any, response)
        if hasattr(response_any, 'additional_kwargs'):
            reasoning = response_any.additional_kwargs.get('reasoning_content', '')
            if reasoning:
                logger.info(f"[Agent Node] 检测到 reasoning，长度: {len(reasoning)}")
        
        return {
            "messages": [response],
            "tool_call_count": tool_count,
            "reasoning": reasoning,
            "stock_query": state.get("stock_query", ""),
            "final_result": state.get("final_result", ""),
            "conversation_id": state.get("conversation_id", ""),
            "doom_loop_detected": False
        }  # type: ignore[return-value]
    
    return agent_node


def should_continue(state: AgentState, max_tool_calls: int = MAX_TOOL_CALLS_DEFAULT) -> str:
    """判断是否继续工具调用循环"""
    current_count = state.get("tool_call_count", 0)
    
    if current_count >= max_tool_calls:
        logger.warning(f"[should_continue] 达到最大工具调用次数 ({max_tool_calls})，强制结束")
        return "end"
    
    messages = state.get("messages", [])
    if not messages:
        return "end"
    
    last_message = messages[-1]
    
    if _check_doom_loop(messages):
        logger.warning("[should_continue] 检测到 doom loop: 连续调用相同工具")
        return "ask_user"
    
    tool_calls = _get_tool_calls(last_message)
    if tool_calls:
        tool_names = [tc.get('name', 'unknown') for tc in tool_calls]
        logger.info(f"[should_continue] 检测到 tool_calls: {tool_names}")
        return "tools"
    
    logger.info("[should_continue] 无 tool_calls，返回最终结果")
    return "end"


def end_node(state: AgentState) -> AgentState:
    """结束节点 - 提取最终回复"""
    messages = state.get("messages", [])
    doom_loop = _check_doom_loop(messages)
    
    ai_messages = [m for m in messages if isinstance(m, AIMessage) and m.content]
    logger.info(f"[End Node] 共找到 {len(ai_messages)} 条 AIMessage")
    
    final_content = ai_messages[-1].content if ai_messages else ""
    reasoning = _extract_reasoning(messages)
    
    final_str = str(final_content) if final_content else ""
    reasoning_str = str(reasoning) if reasoning else ""
    
    if doom_loop:
        logger.warning("[End Node] 检测到 doom loop 结束")
    
    if final_content:
        logger.info(f"[End Node] 使用最后一条 AIMessage，长度: {len(final_str)}")
    if reasoning:
        logger.info(f"[End Node] 提取 reasoning，长度: {len(reasoning_str)}")
    
    return AgentState(
        messages=list(state.get("messages", [])),  # type: ignore[arg-type]
        final_result=final_str,
        reasoning=reasoning_str,
        stock_query=state.get("stock_query", ""),
        tool_call_count=state.get("tool_call_count", 0),
        conversation_id=state.get("conversation_id", ""),
        doom_loop_detected=doom_loop
    )


def create_stock_agent_graph(
    llm: BaseChatModel,
    tools: List[BaseTool],
    system_prompt: str,
    max_tool_calls: int = MAX_TOOL_CALLS_DEFAULT
) -> Any:
    """创建 LangGraph Agent"""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", create_agent_node(llm, tools, system_prompt))
    workflow.add_node("tools", create_tool_node(tools))
    workflow.add_node("end", end_node)
    
    workflow.add_edge(START, "agent")
    
    workflow.add_conditional_edges(
        "agent",
        lambda state: should_continue(state, max_tool_calls),
        {
            "tools": "tools",
            "end": "end",
            "ask_user": "end"
        }
    )
    
    workflow.add_edge("tools", "agent")
    
    return workflow.compile(checkpointer=MemorySaver())


DEFAULT_STOCK_PROMPT = """你是一位专业的股票分析师，擅长技术分析和基本面分析。

【股票代码格式】
- A股: 600519 (贵州茅台), 000001 (平安银行), 300750 (宁德时代)
- 港股: 00700 (腾讯控股), 09988 (阿里巴巴)
- 美股: AAPL (苹果), GOOGL (谷歌), MSFT (微软)

【重要规则】
1. 当用户询问股票时，你必须调用工具获取数据
2. 绝对不能只回复文字而不调用工具
3. 调用工具后，基于返回数据生成分析报告

【可用的工具】
- get_stock_quote: 查询股票实时行情
- get_stock_daily: 查询股票历史数据
- get_fina_indicator: 查询财务指标

请根据用户的问题选择合适的工具来回答。"""
