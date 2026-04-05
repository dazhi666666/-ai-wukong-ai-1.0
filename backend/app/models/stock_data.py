from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class Quote(Base):
    """实时行情表"""
    __tablename__ = "data_quote"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    data = Column(JSON, nullable=False, default={})
    available = Column(Boolean, default=False)
    reason = Column(String(255), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Daily(Base):
    """日线数据表"""
    __tablename__ = "data_daily"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    data = Column(JSON, nullable=False, default=[])
    available = Column(Boolean, default=False)
    reason = Column(String(255), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Indicator(Base):
    """财务指标表"""
    __tablename__ = "data_indicator"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    data = Column(JSON, nullable=False, default=[])
    available = Column(Boolean, default=False)
    reason = Column(String(255), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Moneyflow(Base):
    """资金流向表"""
    __tablename__ = "data_moneyflow"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    data = Column(JSON, nullable=False, default=[])
    available = Column(Boolean, default=False)
    reason = Column(String(255), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Margin(Base):
    """融资融券表"""
    __tablename__ = "data_margin"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    data = Column(JSON, nullable=False, default=[])
    available = Column(Boolean, default=False)
    reason = Column(String(255), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
