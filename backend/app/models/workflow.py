from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal


class NodeConfig(BaseModel):
    """节点配置"""
    prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    variable_name: Optional[str] = None
    output_key: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None


class NodeData(BaseModel):
    """节点数据"""
    label: str
    type: Literal['start', 'llm', 'end']
    config: Optional[NodeConfig] = None


class Position(BaseModel):
    """节点位置"""
    x: float
    y: float


class Node(BaseModel):
    """工作流节点"""
    id: str
    type: str
    data: NodeData
    position: Position


class Edge(BaseModel):
    """工作流边（连接）"""
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class WorkflowSchema(BaseModel):
    """工作流结构"""
    nodes: List[Node]
    edges: List[Edge]


class WorkflowRunRequest(BaseModel):
    """执行工作流请求"""
    workflow: WorkflowSchema
    inputs: Dict[str, Any] = {}


class WorkflowRunResponse(BaseModel):
    """执行工作流响应"""
    result: str
    node_outputs: Optional[Dict[str, Any]] = None


class WorkflowSaveRequest(BaseModel):
    """保存工作流请求"""
    name: str
    description: Optional[str] = None
    workflow: WorkflowSchema


class WorkflowMetadata(BaseModel):
    """工作流元数据"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
