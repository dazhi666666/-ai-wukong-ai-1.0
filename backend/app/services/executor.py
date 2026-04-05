import logging
import re
import os
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
import httpx

from app.models.workflow import WorkflowSchema, Node, Edge

logger = logging.getLogger("llm_chat.executor")


class WorkflowExecutor:
    """工作流执行引擎"""
    
    @property
    def api_key(self):
        return os.getenv("DEEPSEEK_API_KEY")
    
    @property
    def api_url(self):
        return os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    
    @property
    def default_model(self):
        return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    def __init__(self):
        self.context: Dict[str, Any] = {}
        self.node_outputs: Dict[str, Any] = {}
    
    def topological_sort(self, nodes: List[Node], edges: List[Edge]) -> List[str]:
        """
        拓扑排序：根据边计算节点的执行顺序
        返回节点 ID 的有序列表
        """
        # 构建邻接表和入度表
        node_ids = {node.id for node in nodes}
        adjacency: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = defaultdict(int)
        
        # 初始化所有节点的入度为 0
        for node in nodes:
            in_degree[node.id] = 0
        
        # 构建图结构
        for edge in edges:
            if edge.source in node_ids and edge.target in node_ids:
                adjacency[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        # Kahn 算法进行拓扑排序
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_nodes = []
        
        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_id)
            
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否存在环
        if len(sorted_nodes) != len(nodes):
            raise ValueError("工作流图中存在循环依赖")
        
        return sorted_nodes
    
    def resolve_variables(self, text: str) -> str:
        """
        解析并替换文本中的变量引用
        支持格式：
        - {{start.xxx}} - 引用开始节点的变量
        - {{nodes.id.xxx}} - 引用指定节点的输出
        """
        if not text:
            return text
        
        # 匹配 {{...}} 格式的变量
        pattern = r'\{\{([^}]+)\}\}'
        
        def replace_var(match):
            var_path = match.group(1).strip()
            parts = var_path.split('.')
            
            if len(parts) < 2:
                return match.group(0)
            
            if parts[0] == 'start':
                # 引用开始节点的输入
                var_name = parts[1]
                val = self.context.get('start', {}).get(var_name)
                return str(val) if val is not None else ''
            
            elif parts[0] == 'nodes' and len(parts) >= 3:
                # 引用特定节点的输出
                node_id = parts[1]
                output_key = parts[2]
                node_output = self.node_outputs.get(node_id, {})
                val = node_output.get(output_key)
                return str(val) if val is not None else ''
            
            return match.group(0)
        
        return re.sub(pattern, replace_var, text)
    
    async def execute_llm_node(self, node: Node, prompt: str, model: Optional[str] = None, 
                              temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """执行 LLM 节点，调用 DeepSeek API"""
        api_key = self.api_key
        if not api_key:
            raise ValueError("DeepSeek API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                return data["choices"][0]["message"]["content"]
                
        except httpx.HTTPStatusError as e:
            raise ValueError(f"DeepSeek API error: {e.response.text}")
        except httpx.RequestError as e:
            raise ValueError(f"Failed to connect to DeepSeek API: {str(e)}")
        except Exception as e:
            raise ValueError(f"Internal error: {str(e)}")
    
    async def execute_node(self, node: Node, workflow: WorkflowSchema, execution_order: List[str]) -> Dict[str, Any]:
        """执行单个节点"""
        node_id = node.id
        node_type = node.data.type
        config = node.data.config.model_dump() if node.data.config else {}
        
        output = {}
        
        if node_type == 'start':
            # 开始节点：从 context 中获取输入值
            variable_name = config.get('variable_name', 'user_input')
            output = {
                'value': self.context.get('start', {}).get(variable_name, ''),
                'variable_name': variable_name
            }
        
        elif node_type == 'llm':
            # LLM 节点：解析 Prompt 变量并调用 API
            raw_prompt = config.get('prompt', '')
            resolved_prompt = self.resolve_variables(raw_prompt)
            
            logger.info(f"LLM Node '{node_id}' - Raw prompt: {raw_prompt[:100]}...")
            logger.info(f"LLM Node '{node_id}' - Resolved prompt: {resolved_prompt[:100]}...")
            logger.info(f"LLM Node '{node_id}' - Context: {self.context}")
            
            model = config.get('model', self.default_model)
            temperature = config.get('temperature', 0.7)
            max_tokens = config.get('max_tokens', 2000)
            
            response = await self.execute_llm_node(
                node=node,
                prompt=resolved_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            output = {
                'response': response,
                'prompt': resolved_prompt,
                'model': model
            }
        
        elif node_type == 'end':
            # 结束节点：获取指定输出
            output_key = config.get('output_key', 'result')
            
            # 查找前置节点的输出
            value = None
            
            # 找到当前节点在执行顺序中的位置，获取其前一个节点
            try:
                current_idx = execution_order.index(node_id)
                if current_idx > 0:
                    prev_node_id = execution_order[current_idx - 1]
                    if prev_node_id in self.node_outputs:
                        prev_output = self.node_outputs[prev_node_id]
                        if isinstance(prev_output, dict):
                            if 'response' in prev_output:
                                value = prev_output['response']
                            elif 'value' in prev_output:
                                value = prev_output['value']
            except (ValueError, IndexError):
                pass
            
            output = {
                'result': value or '',
                'output_key': output_key
            }
        
        self.node_outputs[node_id] = output
        return output
    
    async def execute(self, workflow: WorkflowSchema, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整工作流
        
        Args:
            workflow: 工作流定义
            inputs: 初始输入变量
            
        Returns:
            执行结果
        """
        # 重置状态
        self.context = {'start': inputs}
        self.node_outputs = {}
        
        # 获取执行顺序
        execution_order = self.topological_sort(workflow.nodes, workflow.edges)
        
        # 创建节点映射
        node_map = {node.id: node for node in workflow.nodes}
        
        # 按顺序执行节点
        for node_id in execution_order:
            node = node_map[node_id]
            await self.execute_node(node, workflow, execution_order)
        
        # 查找结束节点
        end_node_output = None
        for node_id in execution_order:
            node = node_map[node_id]
            if node.data.type == 'end':
                end_node_output = self.node_outputs.get(node_id, {})
                break
        
        result = end_node_output.get('result', '') if end_node_output else ''
        
        return {
            'result': result,
            'node_outputs': self.node_outputs,
            'execution_order': execution_order
        }


# 全局执行器实例
executor = WorkflowExecutor()


async def run_workflow(workflow: WorkflowSchema, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：执行工作流"""
    return await executor.execute(workflow, inputs)
