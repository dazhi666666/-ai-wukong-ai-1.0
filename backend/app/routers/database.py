from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import os
from pathlib import Path

from app.database import get_db, SessionLocal
from app.models import Conversation, Message, CrawledData, Chart

router = APIRouter(prefix="/database")


@router.get("/stats")
async def get_database_stats(db: Session = Depends(get_db)):
    conv_count = db.query(Conversation).count()
    msg_count = db.query(Message).count()
    crawled_count = db.query(CrawledData).count()
    chart_count = db.query(Chart).count()

    db_path = Path(__file__).parent.parent.parent / "llm_chat.db"
    db_size = "0 KB"
    if db_path.exists():
        size = db_path.stat().st_size
        if size > 1024 * 1024:
            db_size = f"{size / (1024 * 1024):.2f} MB"
        else:
            db_size = f"{size / 1024:.2f} KB"

    return {
        "conversations": conv_count,
        "messages": msg_count,
        "crawled_data": crawled_count,
        "charts": chart_count,
        "db_size": db_size,
        "db_path": str(db_path),
        "tables": [
            {"name": "conversations", "count": conv_count},
            {"name": "messages", "count": msg_count},
            {"name": "crawled_data", "count": crawled_count},
            {"name": "charts", "count": chart_count},
        ]
    }


@router.post("/export")
async def export_database(db: Session = Depends(get_db)):
    import json
    from datetime import datetime

    conversations = db.query(Conversation).all()
    messages = db.query(Message).all()

    export_data = {
        "export_time": datetime.now().isoformat(),
        "conversations": [],
        "messages": [],
    }

    for conv in conversations:
        export_data["conversations"].append({
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        })

    for msg in messages:
        export_data["messages"].append({
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
        })

    export_dir = Path(__file__).parent.parent.parent / "exports"
    export_dir.mkdir(exist_ok=True)

    filename = f"llm_chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    export_path = export_dir / filename

    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    return {
        "status": "success",
        "file": str(export_path),
        "conversations_count": len(export_data["conversations"]),
        "messages_count": len(export_data["messages"]),
    }


@router.post("/clear")
async def clear_database(db: Session = Depends(get_db)):
    db.query(Message).delete()
    db.query(Conversation).delete()
    db.commit()

    return {
        "status": "success",
        "message": "All conversations and messages have been cleared"
    }
