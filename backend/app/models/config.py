from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class ModelCatalogEntry(Base):
    __tablename__ = "model_catalog_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    context_length = Column(Integer, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    input_price_per_1k = Column(Float, default=0)
    output_price_per_1k = Column(Float, default=0)
    currency = Column(String(10), default="CNY")
    is_deprecated = Column(Boolean, default=False)
    capabilities = Column(Text, nullable=True)
    original_provider = Column(String(50), nullable=True)
    original_model = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    api_doc_url = Column(String(255), nullable=True)
    default_base_url = Column(String(255), nullable=True)
    api_key = Column(String(500), nullable=True)
    api_secret = Column(String(500), nullable=True)
    supported_features = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_aggregator = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    configs = relationship("LLMConfig", back_populates="provider_info", cascade="all, delete-orphan")


class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("llm_providers.id"), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    model_display_name = Column(String(200), nullable=True)
    api_base = Column(String(255), nullable=True)
    max_tokens = Column(Integer, default=4000)
    temperature = Column(Float, default=0.7)
    timeout = Column(Integer, default=180)
    retry_times = Column(Integer, default=3)
    enabled = Column(Boolean, default=True)
    enable_memory = Column(String(20), default="full")  # none: 不开启, full: 全量记忆, enhanced: 记忆增强
    enable_debug = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    model_category = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    input_price_per_1k = Column(Float, default=0)
    output_price_per_1k = Column(Float, default=0)
    currency = Column(String(10), default="CNY")
    is_default = Column(Boolean, default=False)
    capability_level = Column(Integer, default=2)
    suitable_roles = Column(Text, nullable=True)
    features = Column(Text, nullable=True)
    recommended_depths = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    provider_info = relationship("LLMProvider", back_populates="configs", foreign_keys=[provider_id])

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
