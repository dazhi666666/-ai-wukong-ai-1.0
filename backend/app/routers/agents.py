import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.agent.agent_service import AgentService
from app.services.agent.executor import AgentExecutor
from app.services.logging_manager import get_logger

logger = get_logger("agents_router")

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    category: str
    version: str = "v1.0"
    icon: str = "🤖"
    input_params: List[dict] = []
    output_params: List[dict] = []
    is_builtin: bool = False


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    icon: Optional[str] = None
    input_params: Optional[List[dict]] = None
    output_params: Optional[List[dict]] = None
    is_active: Optional[bool] = None


class AgentConfigUpdate(BaseModel):
    temperature: float = 0.2
    max_iterations: int = 3
    timeout: int = 300
    tools: List[str] = []


class PromptCreate(BaseModel):
    version_name: str
    version_slug: str
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    tool_instructions: Optional[str] = None
    analysis_requirements: Optional[str] = None
    output_format: Optional[str] = None
    constraints: Optional[str] = None
    available_variables: dict = {}
    is_default: bool = False


class PromptUpdate(BaseModel):
    version_name: Optional[str] = None
    version_slug: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    tool_instructions: Optional[str] = None
    analysis_requirements: Optional[str] = None
    output_format: Optional[str] = None
    constraints: Optional[str] = None
    available_variables: Optional[dict] = None
    is_default: Optional[bool] = None


class AgentExecuteRequest(BaseModel):
    inputs: dict = {}
    prompt_version: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


@router.get("")
async def list_agents(
    category: Optional[str] = Query(None, description="Filter by category"),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db)
):
    service = AgentService(db)
    agents = service.get_all_agents(category=category, include_inactive=include_inactive)
    
    counts = service.get_category_counts()
    
    return {
        "agents": [service.to_dict(a) for a in agents],
        "categories": counts,
        "total": len(agents)
    }


@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    service = AgentService(db)
    counts = service.get_category_counts()
    
    categories = [
        {"name": "全部", "slug": "all", "count": sum(counts.values())},
        {"name": "分析师", "slug": "analyst", "count": counts.get("analyst", 0)},
        {"name": "研究员", "slug": "researcher", "count": counts.get("researcher", 0)},
        {"name": "交易员", "slug": "trader", "count": counts.get("trader", 0)},
        {"name": "风险管理", "slug": "risk", "count": counts.get("risk", 0)},
        {"name": "管理者", "slug": "manager", "count": counts.get("manager", 0)},
    ]
    
    return {"categories": categories}


@router.post("")
async def create_agent(agent_data: AgentCreate, db: Session = Depends(get_db)):
    service = AgentService(db)
    
    existing = service.get_agent_by_slug(agent_data.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Agent with this slug already exists")
    
    agent = service.create_agent(agent_data.model_dump())
    
    return {
        "id": agent.id,
        "name": agent.name,
        "slug": agent.slug,
        "message": "Agent created successfully"
    }


@router.get("/{agent_id}")
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    result = service.to_dict(agent, include_prompts=True, include_config=True)
    
    prompts = service.get_prompts(agent_id)
    result["prompt_details"] = []
    for p in prompts:
        result["prompt_details"].append({
            "id": p.id,
            "version_name": p.version_name,
            "version_slug": p.version_slug,
            "system_prompt": p.system_prompt,
            "user_prompt": p.user_prompt,
            "tool_instructions": p.tool_instructions,
            "analysis_requirements": p.analysis_requirements,
            "output_format": p.output_format,
            "constraints": p.constraints,
            "available_variables": p.available_variables,
            "is_default": p.is_default
        })
    
    return result


@router.put("/{agent_id}")
async def update_agent(agent_id: int, agent_data: AgentUpdate, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = {k: v for k, v in agent_data.model_dump().items() if v is not None}
    updated = service.update_agent(agent_id, update_data)
    
    return {
        "message": "Agent updated successfully",
        "agent": service.to_dict(updated)
    }


@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.is_builtin:
        raise HTTPException(status_code=400, detail="Cannot delete builtin agent")
    
    success = service.delete_agent(agent_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete agent")
    
    return {"message": "Agent deleted successfully"}


@router.get("/{agent_id}/prompts")
async def get_prompts(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    prompts = service.get_prompts(agent_id)
    
    return {
        "prompts": [{
            "id": p.id,
            "version_name": p.version_name,
            "version_slug": p.version_slug,
            "system_prompt": p.system_prompt,
            "user_prompt": p.user_prompt,
            "tool_instructions": p.tool_instructions,
            "analysis_requirements": p.analysis_requirements,
            "output_format": p.output_format,
            "constraints": p.constraints,
            "available_variables": p.available_variables,
            "is_default": p.is_default,
            "created_at": p.created_at.isoformat() if p.created_at else None
        } for p in prompts]
    }


@router.post("/{agent_id}/prompts")
async def create_prompt(agent_id: int, prompt_data: PromptCreate, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if prompt_data.is_default:
        existing_prompts = service.get_prompts(agent_id)
        for p in existing_prompts:
            if p.is_default:
                p.is_default = False
    
    prompt = service.create_prompt(agent_id, prompt_data.model_dump())
    
    return {
        "id": prompt.id,
        "version_name": prompt.version_name,
        "message": "Prompt created successfully"
    }


@router.put("/{agent_id}/prompts/{prompt_id}")
async def update_prompt(agent_id: int, prompt_id: int, prompt_data: PromptUpdate, db: Session = Depends(get_db)):
    service = AgentService(db)
    
    prompt = service.get_prompt_by_id(prompt_id)
    if not prompt or prompt.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    if prompt_data.is_default:
        existing_prompts = service.get_prompts(agent_id)
        for p in existing_prompts:
            if p.id != prompt_id and p.is_default:
                p.is_default = False
    
    update_data = {k: v for k, v in prompt_data.model_dump().items() if v is not None}
    updated = service.update_prompt(prompt_id, update_data)
    
    return {
        "message": "Prompt updated successfully",
        "prompt": {
            "id": updated.id,
            "version_name": updated.version_name,
            "is_default": updated.is_default
        }
    }


@router.delete("/{agent_id}/prompts/{prompt_id}")
async def delete_prompt(agent_id: int, prompt_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    
    prompt = service.get_prompt_by_id(prompt_id)
    if not prompt or prompt.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    success = service.delete_prompt(prompt_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete prompt")
    
    return {"message": "Prompt deleted successfully"}


@router.get("/{agent_id}/config")
async def get_config(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    config = service.get_config(agent_id)
    
    if not config:
        return {
            "config": {
                "temperature": 0.2,
                "max_iterations": 3,
                "timeout": 300,
                "tools": []
            }
        }
    
    return {
        "config": {
            "temperature": config.temperature,
            "max_iterations": config.max_iterations,
            "timeout": config.timeout,
            "tools": config.tools or []
        }
    }


@router.put("/{agent_id}/config")
async def update_config(agent_id: int, config_data: AgentConfigUpdate, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    config = service.create_or_update_config(agent_id, config_data.model_dump())
    
    return {
        "message": "Config updated successfully",
        "config": {
            "temperature": config.temperature,
            "max_iterations": config.max_iterations,
            "timeout": config.timeout,
            "tools": config.tools or []
        }
    }


@router.post("/{agent_id}/execute")
async def execute_agent(agent_id: int, request: AgentExecuteRequest, db: Session = Depends(get_db)):
    executor = AgentExecutor(db)
    result = await executor.execute(
        agent_id=agent_id,
        inputs=request.inputs,
        prompt_version=request.prompt_version,
        provider=request.provider,
        model=request.model
    )
    
    return result


@router.post("/{agent_id}/execute/stream")
async def execute_agent_stream(agent_id: int, request: AgentExecuteRequest, db: Session = Depends(get_db)):
    executor = AgentExecutor(db)
    
    async def generate():
        async for chunk in executor.execute_stream(
            agent_id=agent_id,
            inputs=request.inputs,
            prompt_version=request.prompt_version,
            provider=request.provider,
            model=request.model
        ):
            yield f"data: {chunk}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")