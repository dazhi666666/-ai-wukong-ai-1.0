from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(8), primary_key=True, index=True)
    title = Column(String(255), default="新对话")
    summary = Column(Text, nullable=True)  # 对话摘要（记忆增强模式用）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    conversation_id = Column(String(8), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
