import logging
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4

from app.models.conversation import Conversation, Message
from app.models.config import LLMConfig
from app.services.llm.factory import LLMFactory, get_llm, get_model_config_from_db
from app.services.llm.memory import MemoryManager, ConversationMemory

logger = logging.getLogger("llm_chat.chat_service")


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.memory_manager = MemoryManager(db)

    def get_memory_mode(self, provider: str, model: str) -> str:
        model_config = get_model_config_from_db(provider, model)
        if model_config and model_config.get("enable_memory"):
            return str(model_config.get("enable_memory"))
        
        config_service = self._get_config_service()
        if config_service:
            config = config_service.get_config_by_provider_model(provider, model)
            if config and config.enable_memory:
                return str(config.enable_memory)
        return "full"

    def get_model_config(self, provider: str, model: str) -> Dict[str, Any]:
        model_config = get_model_config_from_db(provider, model)
        if model_config:
            return model_config
        return {
            "temperature": 0.7,
            "max_tokens": 2000,
            "enable_memory": "full"
        }

    def _get_config_service(self):
        try:
            from app.services.config_service import ConfigService
            return ConfigService(self.db)
        except Exception:
            return None

    def _create_llm(
        self,
        provider: str = "deepseek",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        model_config = self.get_model_config(provider, model or "deepseek-chat")
        
        if temperature is None:
            temperature = model_config.get("temperature", 0.7)
        if max_tokens is None:
            max_tokens = model_config.get("max_tokens", 2000)
        
        return get_llm(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            force_new=True
        )

    async def chat(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        provider: str = "deepseek",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        memory_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        if model is None:
            model = "deepseek-chat"
        
        if memory_mode is None:
            memory_mode = self.get_memory_mode(provider, model)
        
        llm = self._create_llm(provider, model, temperature, max_tokens)
        
        conversation = None
        if conversation_id:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

        if memory_mode == "none":
            messages = [HumanMessage(content=prompt)]
        elif memory_mode == "full":
            messages = []
            if conversation:
                for msg in conversation.messages:
                    if msg.role == "user":
                        messages.append(HumanMessage(content=msg.content))
                    elif msg.role == "assistant":
                        messages.append(AIMessage(content=msg.content))
            messages.append(HumanMessage(content=prompt))
        elif memory_mode == "enhanced":
            messages = MemoryManager.build_messages_with_summary(
                conversation, prompt, recent_limit=2
            )
        else:
            messages = [HumanMessage(content=prompt)]

        request_text = "\n".join([f"{m.type}: {m.content}" for m in messages])
        logger.info(f"=== 发送给LLM的文本 ===\n{request_text}")

        response = await llm.ainvoke(messages)
        response_content = response.content

        logger.info(f"=== LLM回复 ===\n{response_content[:500]}...")

        if conversation and memory_mode != "none":
            user_msg = Message(
                id=str(uuid4()),
                conversation_id=conversation.id,
                role="user",
                content=prompt,
                timestamp=datetime.now()
            )
            assistant_msg = Message(
                id=str(uuid4()),
                conversation_id=conversation.id,
                role="assistant",
                content=response_content,
                timestamp=datetime.now()
            )
            self.db.add(user_msg)
            self.db.add(assistant_msg)
            conversation.updated_at = datetime.now()

            if len(conversation.messages) == 0:
                conversation.title = prompt[:30] + "..." if len(prompt) > 30 else prompt

            self.db.commit()

            if memory_mode == "enhanced" and len(conversation.messages) >= 2:
                summary = await self._generate_summary(conversation, provider, model)
                if summary:
                    conversation.summary = summary
                    self.db.commit()

        usage = {}
        try:
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
        except:
            pass

        return {
            "response": response_content,
            "model": model,
            "usage": usage,
            "request_text": request_text
        }

    async def chat_stream(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        provider: str = "deepseek",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        memory_mode: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if model is None:
            model = "deepseek-chat"
        
        if memory_mode is None:
            memory_mode = self.get_memory_mode(provider, model)
        
        llm = self._create_llm(provider, model, temperature, max_tokens)
        
        conversation = None
        if conversation_id:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

        if memory_mode == "none":
            messages = [HumanMessage(content=prompt)]
        elif memory_mode == "full":
            messages = []
            if conversation:
                for msg in conversation.messages:
                    if msg.role == "user":
                        messages.append(HumanMessage(content=msg.content))
                    elif msg.role == "assistant":
                        messages.append(AIMessage(content=msg.content))
            messages.append(HumanMessage(content=prompt))
        elif memory_mode == "enhanced":
            messages = MemoryManager.build_messages_with_summary(
                conversation, prompt, recent_limit=2
            )
        else:
            messages = [HumanMessage(content=prompt)]

        request_text = "\n".join([f"{m.type}: {m.content}" for m in messages])
        logger.info(f"=== 发送给LLM的文本 ===\n{request_text}")

        full_response = ""
        
        try:
            async for chunk in llm.astream(messages):
                content = chunk.content
                if content:
                    full_response += str(content)
                    yield {"content": str(content)}

            logger.info(f"=== LLM回复 ===\n{full_response[:500]}...")

            yield {"request_text": request_text, "full_response": full_response}

            if conversation and memory_mode != "none":
                user_msg = Message(
                    id=str(uuid4()),
                    conversation_id=conversation.id,
                    role="user",
                    content=prompt,
                    timestamp=datetime.now()
                )
                assistant_msg = Message(
                    id=str(uuid4()),
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_response,
                    timestamp=datetime.now()
                )
                self.db.add(user_msg)
                self.db.add(assistant_msg)
                conversation.updated_at = datetime.now()

                if len(conversation.messages) == 0:
                    conversation.title = prompt[:30] + "..." if len(prompt) > 30 else prompt

                self.db.commit()

                if memory_mode == "enhanced" and len(conversation.messages) >= 2:
                    yield {"summary_generating": True}
                    summary = await self._generate_summary(conversation, provider, model)
                    if summary:
                        conversation.summary = summary
                        self.db.commit()
                        logger.info(f"=== 生成摘要 ===\n{summary}")
                    yield {"summary_generating": False}

            yield {"done": True}

        except Exception as e:
            logger.error(f"Chat stream error: {str(e)}")
            yield {"error": str(e)}

    async def _generate_summary(
        self,
        conversation: Conversation,
        provider: str,
        model: str
    ) -> Optional[str]:
        if not conversation or len(conversation.messages) < 2:
            return None

        all_messages = []
        for msg in conversation.messages:
            all_messages.append(f"{msg.role}: {msg.content}")
        
        conversation_text = "\n".join(all_messages)
        summary_prompt = f"请概括以下对话的核心重要内容，要求简洁明了，不超过100字：\n\n{conversation_text}"

        try:
            summary_llm = self._create_llm(provider, model, temperature=0.5, max_tokens=200)
            response = await summary_llm.ainvoke([HumanMessage(content=summary_prompt)])
            return str(response.content).strip()
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            return None
