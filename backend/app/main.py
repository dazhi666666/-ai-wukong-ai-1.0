from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from backend/.env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Create FastAPI app
app = FastAPI(
    title="LLM Chat API",
    description="API for chatting with DeepSeek LLM",
    version="1.0.0"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/")
async def root():
    return {
        "message": "LLM Chat API is running",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/debug")
async def debug():
    """Debug endpoint to check environment variables"""
    return {
        "api_key_configured": bool(os.getenv("DEEPSEEK_API_KEY")),
        "api_key_prefix": os.getenv("DEEPSEEK_API_KEY", "")[:10] + "..." if os.getenv("DEEPSEEK_API_KEY") else None,
        "api_url": os.getenv("DEEPSEEK_API_URL", "not set"),
        "model": os.getenv("DEEPSEEK_MODEL", "not set")
    }