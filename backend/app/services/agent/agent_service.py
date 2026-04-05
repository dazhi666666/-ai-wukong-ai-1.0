import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.agent import Agent, AgentPrompt, AgentConfig, AgentTool
from app.services.logging_manager import get_logger

logger = get_logger("agent_service")


class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_agents(self, category: Optional[str] = None, include_inactive: bool = False) -> List[Agent]:
        query = self.db.query(Agent)
        if category:
            query = query.filter(Agent.category == category)
        if not include_inactive:
            query = query.filter(Agent.is_active == True)
        return query.order_by(Agent.category, Agent.name).all()

    def get_agent_by_id(self, agent_id: int) -> Optional[Agent]:
        return self.db.query(Agent).filter(Agent.id == agent_id).first()

    def get_agent_by_slug(self, slug: str) -> Optional[Agent]:
        return self.db.query(Agent).filter(Agent.slug == slug).first()

    def create_agent(self, data: Dict[str, Any]) -> Agent:
        agent = Agent(
            name=data["name"],
            slug=data["slug"],
            description=data.get("description"),
            category=data["category"],
            version=data.get("version", "v1.0"),
            icon=data.get("icon", "🤖"),
            input_params=data.get("input_params", []),
            output_params=data.get("output_params", []),
            is_builtin=data.get("is_builtin", False),
            is_active=data.get("is_active", True)
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def update_agent(self, agent_id: int, data: Dict[str, Any]) -> Optional[Agent]:
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            return None
        
        for key, value in data.items():
            if hasattr(agent, key) and key not in ["id", "created_at"]:
                setattr(agent, key, value)
        
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def delete_agent(self, agent_id: int) -> bool:
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            return False
        
        if agent.is_builtin:
            logger.warning(f"Cannot delete builtin agent: {agent.name}")
            return False
        
        self.db.delete(agent)
        self.db.commit()
        return True

    def get_prompts(self, agent_id: int) -> List[AgentPrompt]:
        return self.db.query(AgentPrompt).filter(AgentPrompt.agent_id == agent_id).all()

    def get_prompt_by_id(self, prompt_id: int) -> Optional[AgentPrompt]:
        return self.db.query(AgentPrompt).filter(AgentPrompt.id == prompt_id).first()

    def get_default_prompt(self, agent_id: int) -> Optional[AgentPrompt]:
        return self.db.query(AgentPrompt).filter(
            AgentPrompt.agent_id == agent_id,
            AgentPrompt.is_default == True
        ).first()

    def create_prompt(self, agent_id: int, data: Dict[str, Any]) -> AgentPrompt:
        prompt = AgentPrompt(
            agent_id=agent_id,
            version_name=data["version_name"],
            version_slug=data["version_slug"],
            system_prompt=data.get("system_prompt"),
            user_prompt=data.get("user_prompt"),
            tool_instructions=data.get("tool_instructions"),
            analysis_requirements=data.get("analysis_requirements"),
            output_format=data.get("output_format"),
            constraints=data.get("constraints"),
            available_variables=data.get("available_variables", {}),
            is_default=data.get("is_default", False)
        )
        self.db.add(prompt)
        self.db.commit()
        self.db.refresh(prompt)
        return prompt

    def update_prompt(self, prompt_id: int, data: Dict[str, Any]) -> Optional[AgentPrompt]:
        prompt = self.get_prompt_by_id(prompt_id)
        if not prompt:
            return None
        
        for key, value in data.items():
            if hasattr(prompt, key) and key not in ["id", "agent_id", "created_at"]:
                setattr(prompt, key, value)
        
        self.db.commit()
        self.db.refresh(prompt)
        return prompt

    def delete_prompt(self, prompt_id: int) -> bool:
        prompt = self.get_prompt_by_id(prompt_id)
        if not prompt:
            return False
        
        self.db.delete(prompt)
        self.db.commit()
        return True

    def get_config(self, agent_id: int) -> Optional[AgentConfig]:
        return self.db.query(AgentConfig).filter(AgentConfig.agent_id == agent_id).first()

    def create_or_update_config(self, agent_id: int, data: Dict[str, Any]) -> AgentConfig:
        config = self.get_config(agent_id)
        if config:
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        else:
            config = AgentConfig(
                agent_id=agent_id,
                temperature=data.get("temperature", 0.2),
                max_iterations=data.get("max_iterations", 3),
                timeout=data.get("timeout", 300),
                tools=data.get("tools", [])
            )
            self.db.add(config)
        
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_tools(self, agent_id: int) -> List[AgentTool]:
        return self.db.query(AgentTool).filter(AgentTool.agent_id == agent_id).all()

    def set_tools(self, agent_id: int, tools: List[Dict[str, Any]]) -> List[AgentTool]:
        existing = self.get_tools(agent_id)
        for tool in existing:
            self.db.delete(tool)
        
        new_tools = []
        for tool_data in tools:
            tool = AgentTool(
                agent_id=agent_id,
                tool_id=tool_data["tool_id"],
                tool_name=tool_data.get("tool_name", tool_data["tool_id"]),
                description=tool_data.get("description"),
                is_required=tool_data.get("is_required", False)
            )
            self.db.add(tool)
            new_tools.append(tool)
        
        self.db.commit()
        return new_tools

    def get_category_counts(self) -> Dict[str, int]:
        agents = self.db.query(Agent).filter(Agent.is_active == True).all()
        counts = {}
        for agent in agents:
            counts[agent.category] = counts.get(agent.category, 0) + 1
        return counts

    def to_dict(self, agent: Agent, include_prompts: bool = True, include_config: bool = True) -> Dict[str, Any]:
        result = {
            "id": agent.id,
            "name": agent.name,
            "slug": agent.slug,
            "description": agent.description,
            "category": agent.category,
            "version": agent.version,
            "icon": agent.icon,
            "input_params": agent.input_params or [],
            "output_params": agent.output_params or [],
            "is_builtin": agent.is_builtin,
            "is_active": agent.is_active,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
        }
        
        if include_prompts:
            prompts = self.get_prompts(agent.id)
            result["prompts"] = [{
                "id": p.id,
                "version_name": p.version_name,
                "version_slug": p.version_slug,
                "is_default": p.is_default,
                "created_at": p.created_at.isoformat() if p.created_at else None
            } for p in prompts]
        
        if include_config:
            config = self.get_config(agent.id)
            if config:
                result["config"] = {
                    "temperature": config.temperature,
                    "max_iterations": config.max_iterations,
                    "timeout": config.timeout,
                    "tools": config.tools or []
                }
        
        return result