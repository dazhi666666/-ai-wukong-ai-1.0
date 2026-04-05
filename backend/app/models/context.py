from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base

class ContextVariable(Base):
    __tablename__ = "context_variables"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    type = Column(String(50), nullable=False)  # quote, daily, indicator, moneyflow, margin, hsgt, etf
    symbol = Column(String(20), nullable=True)
    provider = Column(String(50), nullable=True)
    data = Column(JSON, nullable=False)
    available = Column(Boolean, default=True)  # 数据是否可用
    reason = Column(String(255), nullable=True)  # 不可用原因
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
