import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.utils.function_calling import convert_to_openai_function

from app.services.llm.chat_service import ChatService
from app.services.llm.factory import get_llm_with_tools, get_llm
from app.services.llm.tools import get_registry, STOCK_TOOLS, PROVIDER_TOOLS
from app.services.config_service import ConfigService
from app.services.logging_manager import get_logger

logger = get_logger("agent_executor")


class AgentExecutor:
    def __init__(self, db: Session):
        self.db = db
        self.chat_service = ChatService(db)
        self.tool_registry = get_registry()
        self._config_service = None

    @property
    def config_service(self):
        if self._config_service is None:
            self._config_service = ConfigService(self.db)
        return self._config_service

    def _get_default_provider_model(self) -> tuple[str, str]:
        default_config = self.config_service.get_default_config()
        if default_config:
            return default_config.provider, default_config.model_name
        return "deepseek", "deepseek-chat"

    def _build_prompt(
        self, 
        prompt_obj: Any, 
        inputs: Dict[str, Any],
        agent_name: str
    ) -> str:
        variables = prompt_obj.available_variables or {}
        
        system_prompt = prompt_obj.system_prompt or ""
        user_prompt = prompt_obj.user_prompt or ""
        
        for var_name, var_info in variables.items():
            placeholder = f"{{{var_name}}}"
            if var_name in inputs:
                value = inputs[var_name]
            elif var_info.get("default"):
                value = var_info["default"]
            else:
                value = var_info.get("description", "")
            
            system_prompt = system_prompt.replace(placeholder, str(value))
            user_prompt = user_prompt.replace(placeholder, str(value))
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        system_prompt = system_prompt.replace("{current_date}", current_date)
        user_prompt = user_prompt.replace("{current_date}", current_date)
        
        if "{tool_names}" in system_prompt:
            tools = self._get_available_tools([])
            tool_names = ", ".join([t.name for t in tools])
            system_prompt = system_prompt.replace("{tool_names}", tool_names)
        
        final_prompt = system_prompt
        if user_prompt:
            final_prompt += "\n\n" + user_prompt
        
        if prompt_obj.tool_instructions:
            final_prompt += "\n\n" + prompt_obj.tool_instructions
        
        return final_prompt

    def _get_available_tools(self, tool_ids: List[str] = None) -> List[Any]:
        """获取可用的工具，优先使用注册表中启用的工具"""
        from app.services.llm.tools import get_registry
        
        try:
            registry = get_registry()
            # 获取注册表中启用的工具函数（LangChain工具）
            enabled_tools = registry.get_enabled_tool_functions()
            
            if enabled_tools:
                logger.info(f"Using {len(enabled_tools)} enabled tools from registry: {[t.name.encode('ascii', 'replace').decode('ascii') for t in enabled_tools]}")
                return enabled_tools
            else:
                logger.warning("No enabled tools found in registry")
        except Exception as e:
            logger.warning(f"Failed to get enabled tools from registry: {e}")
        
        # 后备：使用原来的逻辑
        all_tools = PROVIDER_TOOLS if PROVIDER_TOOLS else STOCK_TOOLS
        
        if tool_ids:
            available = []
            for tool in all_tools:
                tool_name = tool.name.replace("get_", "")
                if tool_name in tool_ids:
                    available.append(tool)
            return available if available else all_tools[:5]
        
        return all_tools[:5]

    async def execute(
        self,
        agent_id: int,
        inputs: Dict[str, Any],
        prompt_version: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        from app.models.agent import Agent, AgentPrompt, AgentConfig
        
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return {"error": "Agent not found"}
        
        config = self.db.query(AgentConfig).filter(AgentConfig.agent_id == agent_id).first()
        
        prompt_query = self.db.query(AgentPrompt).filter(AgentPrompt.agent_id == agent_id)
        if prompt_version:
            prompt_query = prompt_query.filter(AgentPrompt.version_slug == prompt_version)
        
        prompt_obj = prompt_query.filter(AgentPrompt.is_default == True).first()
        if not prompt_obj:
            prompt_obj = prompt_query.first()
        
        if not prompt_obj:
            return {"error": "No prompt found for agent"}
        
        if not provider or not model:
            provider, model = self._get_default_provider_model()
        
        temperature = config.temperature if config else 0.2
        tool_ids = config.tools if config and config.tools else []
        
        tools = self._get_available_tools(tool_ids)
        
        final_prompt = self._build_prompt(prompt_obj, inputs, agent.name)
        
        try:
            if tools:
                llm = get_llm_with_tools(
                    provider=provider,
                    model=model,
                    tools=tools,
                    temperature=temperature,
                    force_new=True
                )
            else:
                llm = get_llm(
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    force_new=True
                )
            
            messages = [HumanMessage(content=final_prompt)]
            response = llm.invoke(messages)
            
            return {
                "success": True,
                "agent_name": agent.name,
                "prompt_version": prompt_obj.version_name,
                "result": response.content if hasattr(response, "content") else str(response),
                "provider": provider,
                "model": model
            }
            
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_name": agent.name
            }

    async def execute_stream(
        self,
        agent_id: int,
        inputs: Dict[str, Any],
        prompt_version: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ):
        from app.models.agent import Agent, AgentPrompt, AgentConfig
        
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            yield {"error": "Agent not found"}
            return
        
        config = self.db.query(AgentConfig).filter(AgentConfig.agent_id == agent_id).first()
        
        prompt_query = self.db.query(AgentPrompt).filter(AgentPrompt.agent_id == agent_id)
        if prompt_version:
            prompt_query = prompt_query.filter(AgentPrompt.version_slug == prompt_version)
        
        prompt_obj = prompt_query.filter(AgentPrompt.is_default == True).first()
        if not prompt_obj:
            prompt_obj = prompt_query.first()
        
        if not prompt_obj:
            yield {"error": "No prompt found for agent"}
            return
        
        if not provider or not model:
            provider, model = self._get_default_provider_model()
        
        temperature = config.temperature if config else 0.2
        tool_ids = config.tools if config and config.tools else []
        
        tools = self._get_available_tools(tool_ids)
        final_prompt = self._build_prompt(prompt_obj, inputs, agent.name)
        
        try:
            if tools:
                llm = get_llm_with_tools(
                    provider=provider,
                    model=model,
                    tools=tools,
                    temperature=temperature,
                    force_new=True
                )
            else:
                llm = get_llm(
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    force_new=True
                )
            
            messages = [HumanMessage(content=final_prompt)]
            
            for chunk in llm.stream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    yield {"chunk": chunk.content}
                elif chunk:
                    yield {"chunk": str(chunk)}
            
            yield {"done": True}
            
        except Exception as e:
            logger.error(f"Agent execution stream error: {e}")
            yield {"error": str(e)}