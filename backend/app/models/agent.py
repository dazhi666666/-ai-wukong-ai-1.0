from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    version = Column(String(20), default="v1.0")
    icon = Column(String(50), default="🤖")
    
    input_params = Column(JSON, default=list)
    output_params = Column(JSON, default=list)
    
    is_builtin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    prompts = relationship("AgentPrompt", back_populates="agent", cascade="all, delete-orphan")
    configs = relationship("AgentConfig", back_populates="agent", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class AgentPrompt(Base):
    __tablename__ = "agent_prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    version_name = Column(String(50), nullable=False)
    version_slug = Column(String(50), nullable=False)
    
    system_prompt = Column(Text, nullable=True)
    user_prompt = Column(Text, nullable=True)
    tool_instructions = Column(Text, nullable=True)
    analysis_requirements = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    constraints = Column(Text, nullable=True)
    
    available_variables = Column(JSON, default=dict)
    
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    agent = relationship("Agent", back_populates="prompts")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    temperature = Column(Float, default=0.2)
    max_iterations = Column(Integer, default=3)
    timeout = Column(Integer, default=300)
    
    tools = Column(JSON, default=list)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    agent = relationship("Agent", back_populates="configs")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class AgentTool(Base):
    __tablename__ = "agent_tools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    tool_id = Column(String(100), nullable=False)
    tool_name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    
    is_required = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )