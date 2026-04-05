import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
import asyncio

from app.database import get_db
from app.models import Conversation, Message, RequestLog
from app.models.config import LLMConfig
from app.schemas import ConversationCreate
from app.services.config_service import ConfigService
from app.services.llm.chat_service import ChatService

LOG_FILE = "data/request_logs.txt"

def write_to_log_file(request_content: str, response_content: str, summary: str, memory_mode: str, model: str):
    try:
        import os
        os.makedirs("data", exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"记忆模式: {memory_mode or 'unknown'}\n")
            f.write(f"模型: {model or 'unknown'}\n")
            f.write("-" * 40 + "\n")
            f.write("【发送给LLM的文本】\n")
            f.write(request_content or "")
            f.write("\n")
            f.write("-" * 40 + "\n")
            f.write("【LLM回复】\n")
            f.write(response_content or "")
            f.write("\n")
            if summary:
                f.write("-" * 40 + "\n")
                f.write("【摘要】\n")
                f.write(summary)
                f.write("\n")
            f.write("\n")
    except Exception as e:
        logging.error(f"写入日志文件失败: {str(e)}")

router = APIRouter()
logger = logging.getLogger("llm_chat.chat")

DEEPSEEK_MODEL = "deepseek-chat"


class ChatRequest(BaseModel):
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 2000
    conversation_id: Optional[str] = None
    model: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    model: str
    usage: Optional[dict] = None


def get_memory_mode_from_config(db: Session, provider: str, model: Optional[str]) -> str:
    if model:
        config_service = ConfigService(db)
        config = config_service.get_config_by_provider_model(provider, model)
        if config and config.enable_memory:
            return str(config.enable_memory)
    return "full"


@router.post("/conversations")
async def create_conversation(data: ConversationCreate, db: Session = Depends(get_db)):
    conv_id = str(uuid4())[:8]
    now = datetime.now()
    title = data.title or f"新对话 {uuid4().hex[:4]}"

    conversation = Conversation(
        id=conv_id,
        title=title,
        created_at=now,
        updated_at=now
    )
    db.add(conversation)
    db.commit()

    return {"id": conv_id, "title": title}


@router.get("/conversations")
async def get_conversations(db: Session = Depends(get_db)):
    conversations = db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
    result = []
    for conv in conversations:
        result.append({
            "id": conv.id,
            "title": conv.title,
            "message_count": len(conv.messages),
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        })
    return result


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = []
    for msg in conversation.messages:
        messages.append({
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        })

    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": messages,
        "summary": conversation.summary,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat()
    }


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    db.delete(conversation)
    db.commit()
    return {"status": "deleted"}


@router.post("/chat", response_model=ChatResponse)
async def chat_with_llm(request: ChatRequest, db: Session = Depends(get_db)):
    provider = "deepseek"
    model = request.model if request.model else DEEPSEEK_MODEL
    
    memory_mode = get_memory_mode_from_config(db, provider, model)
    
    chat_service = ChatService(db)
    
    try:
        result = await chat_service.chat(
            prompt=request.prompt,
            conversation_id=request.conversation_id,
            provider=provider,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            memory_mode=memory_mode
        )
        
        conversation = None
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id
            ).first()
        
        if conversation:
            request_log = RequestLog(
                conversation_id=conversation.id,
                request_content=result.get("request_text", f"user: {request.prompt}"),
                response_content=result["response"],
                summary=conversation.summary or "",
                memory_mode=memory_mode,
                model=model
            )
            db.add(request_log)
            db.commit()
            write_to_log_file(
                result.get("request_text", f"user: {request.prompt}"),
                result["response"],
                conversation.summary or "",
                memory_mode,
                model
            )

        return ChatResponse(
            response=result["response"],
            model=result["model"],
            usage=result.get("usage")
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


async def stream_generator(
    prompt: str,
    conversation_id: Optional[str],
    provider: str,
    model: Optional[str],
    temperature: float,
    max_tokens: int,
    memory_mode: str,
    db: Session
):
    chat_service = ChatService(db)
    
    conversation = None
    if conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
    
    full_request_text = None
    full_response = None
    
    try:
        async for chunk in chat_service.chat_stream(
            prompt=prompt,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            memory_mode=memory_mode
        ):
            if "content" in chunk:
                yield f"data: {json.dumps({'content': chunk['content']})}\n\n"
            elif "summary_generating" in chunk:
                yield f"data: {json.dumps({'summary_generating': chunk['summary_generating']})}\n\n"
            elif "request_text" in chunk and "full_response" in chunk:
                full_request_text = chunk["request_text"]
                full_response = chunk["full_response"]
            elif chunk.get("done"):
                yield f"data: {json.dumps({'done': True})}\n\n"
            elif "error" in chunk:
                yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
        
        if conversation and full_request_text and full_response:
            db.refresh(conversation)
            generated_summary = conversation.summary
            
            request_log = RequestLog(
                conversation_id=conversation.id,
                request_content=full_request_text,
                response_content=full_response,
                summary=generated_summary or "",
                memory_mode=memory_mode,
                model=model
            )
            db.add(request_log)
            db.commit()
            
            write_to_log_file(
                full_request_text,
                full_response,
                generated_summary or "",
                memory_mode,
                model
            )

    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    provider = "deepseek"
    model = request.model if request.model else DEEPSEEK_MODEL
    model = model or DEEPSEEK_MODEL
    
    memory_mode = get_memory_mode_from_config(db, provider, model)

    return StreamingResponse(
        stream_generator(
            prompt=request.prompt,
            conversation_id=request.conversation_id,
            provider=provider,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            memory_mode=memory_mode,
            db=db
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
