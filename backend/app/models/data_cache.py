from sqlalchemy import Column, String, Text, DateTime, JSON, Integer
from sqlalchemy.sql import func
from app.database.session import Base


class DataCache(Base):
    __tablename__ = "data_cache"

    cache_key = Column(String(100), primary_key=True)
    data_type = Column(String(50))
    stock_code = Column(String(20))
    data = Column(JSON)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    hit_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<DataCache {self.cache_key}>"
