from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4

from app.database import get_db
from app.models import Workflow
from app.models.workflow import (
    WorkflowSchema,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowSaveRequest,
    WorkflowMetadata
)
from app.services.workflow.langgraph_executor import run_workflow

router = APIRouter()


@router.post("/workflows/run", response_model=WorkflowRunResponse)
async def execute_workflow(request: WorkflowRunRequest):
    """
    执行工作流 (使用 LangGraph)
    
    输入: 
    - workflow: 工作流结构（节点和边）
    - inputs: 初始输入变量，如 {"user_input": "你好"}
    
    输出:
    - result: 最终结果
    - node_outputs: 各节点输出
    """
    try:
        result = await run_workflow(request.workflow, request.inputs)
        if isinstance(result, dict):
            return WorkflowRunResponse(
                result=result.get('result', ''),
                node_outputs=result.get('node_outputs', {})
            )
        else:
            return WorkflowRunResponse(
                result=str(result) if result else '',
                node_outputs={}
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")


@router.post("/workflows/save")
async def save_workflow(request: WorkflowSaveRequest, db: Session = Depends(get_db)):
    """
    保存工作流配置
    
    输入:
    - name: 工作流名称
    - description: 工作流描述（可选）
    - workflow: 工作流结构
    
    输出:
    - id: 工作流 ID
    - message: 保存成功消息
    """
    workflow_id = str(uuid4())[:8]
    
    workflow = Workflow(
        id=workflow_id,
        name=request.name or "未命名工作流",
        description=request.description,
        nodes=[node.model_dump() for node in request.workflow.nodes],
        edges=[edge.model_dump() for edge in request.workflow.edges]
    )
    
    db.add(workflow)
    db.commit()
    
    return {
        "id": workflow_id,
        "message": "工作流保存成功"
    }


@router.get("/workflows")
async def list_workflows(db: Session = Depends(get_db)):
    """
    获取工作流列表
    
    输出: 工作流元数据列表
    """
    workflows = db.query(Workflow).order_by(Workflow.updated_at.desc()).all()
    
    result = []
    for wf in workflows:
        result.append({
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "created_at": wf.created_at.isoformat() if wf.created_at else None,
            "updated_at": wf.updated_at.isoformat() if wf.updated_at else None
        })
    
    return result


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """
    加载指定工作流配置
    
    输入: workflow_id - 工作流 ID
    
    输出: 完整的工作流配置
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "workflow": {
            "nodes": workflow.nodes or [],
            "edges": workflow.edges or []
        },
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
    }


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """
    删除工作流
    
    输入: workflow_id - 工作流 ID
    
    输出: 删除成功消息
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    db.delete(workflow)
    db.commit()
    
    return {"message": "工作流删除成功"}
