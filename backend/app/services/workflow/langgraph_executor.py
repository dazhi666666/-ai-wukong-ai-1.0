import logging
import re
import uuid
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from pydantic import BaseModel

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from app.models.workflow import WorkflowSchema, Node, Edge
from app.services.llm.factory import get_llm

logger = logging.getLogger("llm_chat.workflow")

DEFAULT_MODEL = "deepseek-chat"
DEFAULT_PROVIDER = "deepseek"


class WorkflowState(BaseModel):
    """工作流状态"""
    inputs: Dict[str, Any] = {}
    node_outputs: Dict[str, Any] = {}
    current_node: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None


class LangGraphWorkflowExecutor:
    """基于 LangGraph 的工作流执行器"""
    
    def __init__(
        self,
        provider: str = DEFAULT_PROVIDER,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.graph: Optional[StateGraph] = None
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
        
    def _get_llm(self):
        return get_llm(
            provider=self.provider,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
    
    def _resolve_variables(self, text: str, context: Dict[str, Any], node_outputs: Dict[str, Any]) -> str:
        """解析变量引用"""
        if not text:
            return text
        
        pattern = r'\{\{([^}]+)\}\}'
        
        def replace_var(match):
            var_path = match.group(1).strip()
            parts = var_path.split('.')
            
            if len(parts) < 2:
                return match.group(0)
            
            if parts[0] == 'start':
                var_name = parts[1]
                val = context.get(var_name)
                return str(val) if val is not None else ''
            
            elif parts[0] == 'nodes' and len(parts) >= 3:
                node_id = parts[1]
                output_key = parts[2]
                output = node_outputs.get(node_id, {})
                val = output.get(output_key)
                return str(val) if val is not None else ''
            
            elif parts[0] == 'inputs':
                var_name = parts[1]
                val = context.get(var_name)
                return str(val) if val is not None else ''
            
            return match.group(0)
        
        return re.sub(pattern, replace_var, text)
    
    def _build_node_function(self, node: Node):
        """为节点构建执行函数"""
        node_id = node.id
        node_type = node.data.type
        config = node.data.config.model_dump() if node.data.config else {}
        
        def node_func(state: WorkflowState) -> WorkflowState:
            new_outputs = dict(state.node_outputs)
            
            if node_type == 'start':
                variable_name = config.get('variable_name', 'input')
                value = state.inputs.get(variable_name, '')
                new_outputs[node_id] = {
                    'value': value,
                    'variable_name': variable_name
                }
                logger.info(f"Start node '{node_id}': {variable_name}={value}")
            
            elif node_type == 'llm':
                raw_prompt = config.get('prompt', '')
                resolved_prompt = self._resolve_variables(raw_prompt, state.inputs, new_outputs)
                
                model = config.get('model', self.model)
                temperature = config.get('temperature', self.temperature)
                max_tokens = config.get('max_tokens', self.max_tokens)
                
                logger.info(f"LLM Node '{node_id}' prompt: {resolved_prompt[:100]}...")
                
                try:
                    llm = get_llm(
                        provider=self.provider,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    import asyncio
                    response = asyncio.run(llm.ainvoke([HumanMessage(content=resolved_prompt)]))
                    response_text = response.content
                    
                    new_outputs[node_id] = {
                        'response': response_text,
                        'prompt': resolved_prompt,
                        'model': model
                    }
                    logger.info(f"LLM Node '{node_id}' response: {response_text[:100]}...")
                    
                except Exception as e:
                    logger.error(f"LLM Node '{node_id}' error: {str(e)}")
                    new_outputs[node_id] = {
                        'error': str(e),
                        'prompt': resolved_prompt,
                        'model': model
                    }
            
            elif node_type == 'end':
                output_key = config.get('output_key', 'result')
                
                source_node_id = None
                for edge in self.edges:
                    if edge.target == node_id:
                        source_node_id = edge.source
                        break
                
                if source_node_id and source_node_id in new_outputs:
                    source_output = new_outputs[source_node_id]
                    if 'response' in source_output:
                        result = source_output['response']
                    elif 'value' in source_output:
                        result = source_output['value']
                    else:
                        result = str(source_output)
                else:
                    result = ''
                
                new_outputs[node_id] = {
                    'result': result,
                    'output_key': output_key
                }
                logger.info(f"End node '{node_id}': result={result[:100]}...")
            
            return WorkflowState(
                inputs=state.inputs,
                node_outputs=new_outputs,
                current_node=node_id,
                result=state.result,
                error=state.error
            )
        
        return node_func
    
    def _topological_sort(self) -> List[str]:
        """拓扑排序"""
        node_ids = {node.id for node in self.nodes}
        adjacency: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = defaultdict(int)
        
        for node in self.nodes:
            in_degree[node.id] = 0
        
        for edge in self.edges:
            if edge.source in node_ids and edge.target in node_ids:
                adjacency[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_nodes = []
        
        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_id)
            
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(sorted_nodes) != len(node_ids):
            raise ValueError("工作流图中存在循环依赖")
        
        return sorted_nodes
    
    def _build_graph(self):
        """构建 LangGraph"""
        execution_order = self._topological_sort()
        node_map = {node.id: node for node in self.nodes}
        
        graph = StateGraph(WorkflowState)
        
        for node_id in execution_order:
            node = node_map[node_id]
            node_func = self._build_node_function(node)
            graph.add_node(node_id, node_func)
        
        for edge in self.edges:
            if edge.source in node_map and edge.target in node_map:
                graph.add_edge(edge.source, edge.target)
        
        start_nodes = [n.id for n in self.nodes if n.data.type == 'start']
        if start_nodes:
            graph.set_entry_point(start_nodes[0])
        
        end_nodes = [n.id for n in self.nodes if n.data.type == 'end']
        if end_nodes:
            for end_node in end_nodes:
                graph.add_edge(end_node, END)
        
        return graph
    
    async def execute(self, workflow: WorkflowSchema, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        self.nodes = workflow.nodes
        self.edges = workflow.edges
        
        self.graph = self._build_graph()
        
        checkpointer = MemorySaver()
        compiled_graph = self.graph.compile(checkpointer=checkpointer)
        
        initial_state = WorkflowState(
            inputs=inputs,
            node_outputs={},
            current_node=None,
            result=None,
            error=None
        )
        
        try:
            thread_id = str(uuid.uuid4())
            final_state = await compiled_graph.ainvoke(
                initial_state,
                config={"recursion_limit": 100, "configurable": {"thread_id": thread_id}}
            )
            
            end_nodes = [n for n in self.nodes if n.data.type == 'end']
            result = ""
            if end_nodes:
                node_outputs = final_state.get('node_outputs', {}) if isinstance(final_state, dict) else final_state.node_outputs
                end_output = node_outputs.get(end_nodes[0].id, {})
                result = end_output.get('result', '')
            
            return {
                'result': result,
                'node_outputs': final_state.get('node_outputs', {}) if isinstance(final_state, dict) else final_state.node_outputs,
                'execution_order': [n.id for n in self.nodes]
            }
            
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            raise ValueError(f"工作流执行失败: {str(e)}")


_executor: Optional[LangGraphWorkflowExecutor] = None


def get_executor(
    provider: str = DEFAULT_PROVIDER,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> LangGraphWorkflowExecutor:
    global _executor
    if _executor is None:
        _executor = LangGraphWorkflowExecutor(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    return _executor


async def run_workflow(
    workflow: WorkflowSchema,
    inputs: Dict[str, Any],
    provider: str = DEFAULT_PROVIDER,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> Dict[str, Any]:
    """便捷函数：执行工作流"""
    executor = LangGraphWorkflowExecutor(
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return await executor.execute(workflow, inputs)
