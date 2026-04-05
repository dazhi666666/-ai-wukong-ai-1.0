from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

router = APIRouter()

LOG_FILE = Path(__file__).parent.parent.parent / "app.log"
USER_ACTION_LOG_FILE = Path(__file__).parent.parent.parent / "user_actions.log"

class LogEntry(BaseModel):
    timestamp: str
    level: str
    module: str
    message: str

class LogsResponse(BaseModel):
    logs: List[dict]
    total: int

class UserAction(BaseModel):
    action: str
    details: Optional[str] = None
    user_id: Optional[str] = "default_user"

def parse_log_file(max_lines: int = 500) -> List[dict]:
    logs = []
    if not LOG_FILE.exists():
        return logs
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-max_lines:]:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    parts = line.split(' - ', 3)
                    if len(parts) >= 4:
                        logs.append({
                            "timestamp": parts[0],
                            "level": parts[1],
                            "module": parts[2],
                            "message": parts[3]
                        })
                    elif len(parts) == 3:
                        logs.append({
                            "timestamp": parts[0],
                            "level": parts[1],
                            "module": "",
                            "message": parts[2]
                        })
                    else:
                        logs.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "level": "INFO",
                            "module": "",
                            "message": line
                        })
                except Exception:
                    logs.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "level": "INFO",
                        "module": "",
                        "message": line
                    })
    except Exception as e:
        pass
    
    return list(reversed(logs))

@router.get("/logs", response_model=LogsResponse)
async def get_logs(max_lines: int = 500):
    logs = parse_log_file(max_lines)
    return LogsResponse(logs=logs, total=len(logs))

@router.post("/logs/clear")
async def clear_logs():
    try:
        if LOG_FILE.exists():
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                f.write("")
        return {"status": "success", "message": "日志已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/download")
async def download_logs():
    if not LOG_FILE.exists():
        raise HTTPException(status_code=404, detail="日志文件不存在")
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content, "filename": f"app-logs-{datetime.now().strftime('%Y%m%d')}.log"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logs/user-action")
async def log_user_action(action: UserAction):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - USER_ACTION | {action.user_id} | {action.action}"
    if action.details:
        log_message += f" | {action.details}"
    
    try:
        with open(USER_ACTION_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
        
        # Also log to main app log
        logging.getLogger("llm_chat").info(log_message)
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/user-actions")
async def get_user_actions(max_lines: int = 500):
    if not USER_ACTION_LOG_FILE.exists():
        return {"logs": [], "total": 0}
    
    try:
        with open(USER_ACTION_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        logs = []
        for line in lines[-max_lines:]:
            line = line.strip()
            if line:
                parts = line.split(' | ')
                if len(parts) >= 3:
                    logs.append({
                        "timestamp": parts[0],
                        "user_id": parts[1],
                        "action": parts[2],
                        "details": parts[3] if len(parts) > 3 else ""
                    })
        
        return {"logs": list(reversed(logs)), "total": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logs/user-actions/clear")
async def clear_user_actions():
    try:
        if USER_ACTION_LOG_FILE.exists():
            with open(USER_ACTION_LOG_FILE, 'w', encoding='utf-8') as f:
                f.write("")
        return {"status": "success", "message": "用户操作日志已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
