from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import os
import time
from dotenv import load_dotenv
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Import models first to ensure tables are created
from app.database import init_db
import app.models.conversation
import app.models.config
import app.models.workflow_db

# Configure logging
LOG_DIR = Path(__file__).parent.parent
LOG_FILE = LOG_DIR / "app.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10*1024*1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger("llm_chat")
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

# Load environment variables from backend/.env FIRST, before importing routers
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# NOW import routers (after env is loaded)
from app.routers import chat, workflow, logs, database
from app.routers.llm_config import router as config_router

# Create FastAPI app
app = FastAPI(
    title="LLM Chat API",
    description="API for chatting with DeepSeek LLM",
    version="1.0.0"
)

logger.info("=" * 50)
logger.info("LLM Chat API starting up")
logger.info(f"Server Status: RUNNING")
logger.info(f"Server Port: {os.getenv('PORT', '8000')}")
logger.info(f"Server Host: {os.getenv('HOST', '0.0.0.0')}")
logger.info(f"CORS Origins: {os.getenv('CORS_ORIGINS', 'http://localhost:5173')}")
logger.info(f"Log file: {LOG_FILE}")
logger.info(f"DeepSeek API: {os.getenv('DEEPSEEK_API_URL', 'not configured')}")
logger.info(f"DeepSeek Model: {os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')}")
logger.info("=" * 50)

# Initialize database
init_db()
logger.info("Database initialized")

# Auto-initialize preset LLM providers
from app.database.session import SessionLocal
from app.services.config_service import ConfigService, ModelCatalogService
try:
    db = SessionLocal()
    service = ConfigService(db)
    count = service.init_preset_providers()
    if count > 0:
        logger.info(f"Auto-initialized {count} preset LLM providers")
    
    catalog_service = ModelCatalogService(db)
    catalog_count = catalog_service.init_default_catalogs()
    if catalog_count > 0:
        logger.info(f"Auto-initialized {catalog_count} model catalogs")
    db.close()
except Exception as e:
    logger.warning(f"Failed to auto-initialize: {e}")

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        
        # Log request
        logger.info(f"REQUEST | {method} | {url} | IP: {client_ip}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(f"RESPONSE | {method} | {url} | Status: {response.status_code} | Duration: {duration:.2f}ms")
        
        return response

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(workflow.router, prefix="/api", tags=["workflow"])
app.include_router(logs.router, prefix="/api", tags=["logs"])
app.include_router(database.router, prefix="/api", tags=["database"])
app.include_router(config_router, tags=["config"])

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "LLM Chat API is running",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "server": "running",
        "port": os.getenv("PORT", "8000"),
        "host": os.getenv("HOST", "0.0.0.0"),
        "api_url": os.getenv("DEEPSEEK_API_URL", "not configured"),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "api_key_configured": bool(os.getenv("DEEPSEEK_API_KEY"))
    }

@app.get("/debug")
async def debug():
    """Debug endpoint to check environment variables"""
    return {
        "api_key_configured": bool(os.getenv("DEEPSEEK_API_KEY")),
        "api_key_prefix": os.getenv("DEEPSEEK_API_KEY", "")[:10] + "..." if os.getenv("DEEPSEEK_API_KEY") else None,
        "api_url": os.getenv("DEEPSEEK_API_URL", "not set"),
        "model": os.getenv("DEEPSEEK_MODEL", "not set")
    }