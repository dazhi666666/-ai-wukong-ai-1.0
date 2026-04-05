from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.session import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(8), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)
    request_content = Column(Text)
    response_content = Column(Text)
    summary = Column(Text, nullable=True)
    memory_mode = Column(String(20))
    model = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
