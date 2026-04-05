from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database.session import Base


class CrawledData(Base):
    __tablename__ = "crawled_data"

    id = Column(String(36), primary_key=True)
    source = Column(String(100))
    url = Column(String(500))
    title = Column(String(255))
    content = Column(Text)
    extra_data = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


class Chart(Base):
    __tablename__ = "charts"

    id = Column(String(36), primary_key=True)
    name = Column(String(100))
    chart_type = Column(String(50))
    data = Column(JSON)
    config = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
