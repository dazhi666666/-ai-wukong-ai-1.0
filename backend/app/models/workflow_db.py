from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database.session import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(8), primary_key=True, index=True)
    name = Column(String(255), default="未命名工作流")
    description = Column(Text, nullable=True)
    nodes = Column(JSON, nullable=False, default=list)
    edges = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
