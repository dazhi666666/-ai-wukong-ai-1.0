import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message

logger = logging.getLogger("llm_chat.memory")

RECENT_MESSAGES_LIMIT = 2


class ConversationMemory:
    def __init__(self, db: Session, conversation_id: str, memory_mode: str = "full"):
        self.db = db
        self.conversation_id = conversation_id
        self.memory_mode = memory_mode
        self._history: Optional[InMemoryChatMessageHistory] = None

    def _load_from_db(self) -> InMemoryChatMessageHistory:
        history = InMemoryChatMessageHistory()
        
        conversation = self.db.query(Conversation).filter(
            Conversation.id == self.conversation_id
        ).first()
        
        if not conversation:
            return history

        if self.memory_mode == "full":
            for msg in conversation.messages:
                if msg.role == "user":
                    history.add_user_message(msg.content)
                elif msg.role == "assistant":
                    history.add_ai_message(msg.content)
        
        elif self.memory_mode == "enhanced":
            if conversation.summary:
                history.add_message(SystemMessage(content=f"之前对话摘要：{conversation.summary}"))
            
            recent_msgs = list(conversation.messages)[-RECENT_MESSAGES_LIMIT:]
            for msg in recent_msgs:
                if msg.role == "user":
                    history.add_user_message(msg.content)
                elif msg.role == "assistant":
                    history.add_ai_message(msg.content)

        return history

    @property
    def chat_history(self) -> InMemoryChatMessageHistory:
        if self._history is None:
            self._history = self._load_from_db()
        return self._history

    def add_message(self, role: str, content: str):
        if self.memory_mode == "none":
            return
        
        self.chat_history.add_message(
            HumanMessage(content=content) if role == "user" 
            else AIMessage(content=content)
        )

    def get_messages(self) -> List[BaseMessage]:
        return self.chat_history.messages

    def clear(self):
        self._history = None


class MemoryManager:
    def __init__(self, db: Session):
        self.db = db

    def get_memory(
        self, 
        conversation_id: str, 
        memory_mode: str = "full",
        llm: Optional[Any] = None
    ) -> ConversationMemory:
        return ConversationMemory(self.db, conversation_id, memory_mode)

    def get_conversation_summary(
        self, 
        conversation_id: str, 
        llm: Any
    ) -> Optional[str]:
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return None
        
        return conversation.summary

    def update_summary(
        self, 
        conversation_id: str, 
        summary: str
    ) -> bool:
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return False
        
        conversation.summary = summary
        self.db.commit()
        return True

    @staticmethod
    def build_messages_from_history(
        memory: ConversationMemory,
        current_prompt: str
    ) -> List[BaseMessage]:
        messages = list(memory.get_messages())
        messages.append(HumanMessage(content=current_prompt))
        return messages

    @staticmethod
    def build_messages_with_summary(
        conversation: Optional[Conversation],
        current_prompt: str,
        recent_limit: int = 2
    ) -> List[BaseMessage]:
        messages = []
        
        if conversation and conversation.summary:
            messages.append(SystemMessage(content=f"之前对话摘要：{conversation.summary}"))
        
        if conversation:
            recent_msgs = list(conversation.messages)[-recent_limit:]
            for msg in recent_msgs:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))
        
        messages.append(HumanMessage(content=current_prompt))
        return messages
