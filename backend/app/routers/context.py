import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models.context import ContextVariable
from app.services.logging_manager import get_logger

router = APIRouter()
logger = get_logger("llm_chat.context")


class ContextVariableCreate(BaseModel):
    name: str
    type: str
    symbol: Optional[str] = None
    provider: Optional[str] = None
    data: dict
    available: bool = True
    reason: Optional[str] = None
    description: Optional[str] = None


class ContextVariableResponse(BaseModel):
    id: int
    name: str
    type: str
    symbol: Optional[str]
    provider: Optional[str]
    data: dict
    available: bool
    reason: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# 预定义变量配置
VARIABLE_CONFIGS = {
    "quote": {"type": "quote", "name_prefix": "q_", "description": "实时行情"},
    "daily": {"type": "daily", "name_prefix": "d_", "description": "日线数据"},
    "indicator": {"type": "indicator", "name_prefix": "fi_", "description": "财务指标"},
    "moneyflow": {"type": "moneyflow", "name_prefix": "mf_", "description": "资金流向"},
    "margin": {"type": "margin", "name_prefix": "mg_", "description": "融资融券"},
    "hsgt": {"type": "hsgt", "name_prefix": "", "description": "北向资金"},
    "etf": {"type": "etf", "name_prefix": "", "description": "ETF行情"},
}


@router.get("/variables", response_model=List[ContextVariableResponse])
async def get_all_variables(db: Session = Depends(get_db)):
    """获取所有上下文变量"""
    variables = db.query(ContextVariable).order_by(ContextVariable.created_at.desc()).all()
    return variables


@router.get("/variables/grouped")
async def get_variables_grouped(db: Session = Depends(get_db)):
    """获取按股票代码分组的变量"""
    variables = db.query(ContextVariable).order_by(ContextVariable.created_at.desc()).all()
    
    # 按股票代码分组
    grouped = {}
    for v in variables:
        if v.symbol:
            if v.symbol not in grouped:
                grouped[v.symbol] = []
            grouped[v.symbol].append({
                "name": v.name,
                "type": v.type,
                "available": v.available,
                "reason": v.reason,
                "description": v.description
            })
        else:
            # 全局变量（如 hsgt, etf）
            if "_global" not in grouped:
                grouped["_global"] = []
            grouped["_global"].append({
                "name": v.name,
                "type": v.type,
                "available": v.available,
                "reason": v.reason,
                "description": v.description
            })
    
    return grouped


@router.get("/variables/{name}", response_model=ContextVariableResponse)
async def get_variable(name: str, db: Session = Depends(get_db)):
    """获取指定变量"""
    variable = db.query(ContextVariable).filter(ContextVariable.name == name).first()
    if not variable:
        raise HTTPException(status_code=404, detail=f"Variable '{name}' not found")
    return variable


@router.post("/variables", response_model=ContextVariableResponse)
async def create_variable(var: ContextVariableCreate, db: Session = Depends(get_db)):
    """创建或更新上下文变量"""
    existing = db.query(ContextVariable).filter(ContextVariable.name == var.name).first()
    
    if existing:
        existing.type = var.type
        existing.symbol = var.symbol
        existing.provider = var.provider
        existing.data = var.data
        existing.available = var.available
        existing.reason = var.reason
        existing.description = var.description
        existing.updated_at = datetime.now()
        db.commit()
        db.refresh(existing)
        logger.info(f"Updated context variable: {var.name}")
        return existing
    else:
        new_var = ContextVariable(
            name=var.name,
            type=var.type,
            symbol=var.symbol,
            provider=var.provider,
            data=var.data,
            available=var.available,
            reason=var.reason,
            description=var.description
        )
        db.add(new_var)
        db.commit()
        db.refresh(new_var)
        logger.info(f"Created context variable: {var.name}")
        return new_var


@router.post("/variables/batch")
async def create_variables_batch(vars: List[ContextVariableCreate], db: Session = Depends(get_db)):
    """批量创建或更新上下文变量"""
    results = []
    for var in vars:
        existing = db.query(ContextVariable).filter(ContextVariable.name == var.name).first()
        
        if existing:
            existing.type = var.type
            existing.symbol = var.symbol
            existing.provider = var.provider
            existing.data = var.data
            existing.available = var.available
            existing.reason = var.reason
            existing.description = var.description
            existing.updated_at = datetime.now()
            db.commit()
            db.refresh(existing)
            results.append(existing)
        else:
            new_var = ContextVariable(
                name=var.name,
                type=var.type,
                symbol=var.symbol,
                provider=var.provider,
                data=var.data,
                available=var.available,
                reason=var.reason,
                description=var.description
            )
            db.add(new_var)
            db.commit()
            db.refresh(new_var)
            results.append(new_var)
    
    logger.info(f"Batch created/updated {len(results)} context variables")
    return results


@router.post("/variables/auto/{stock_code}")
async def auto_create_stock_variables(stock_code: str, db: Session = Depends(get_db)):
    """自动为指定股票创建所有预定义变量（初始为不可用状态）"""
    results = []
    
    # 为股票创建变量
    for var_type, config in VARIABLE_CONFIGS.items():
        if var_type in ["hsgt", "etf"]:
            # 全局变量
            var_name = config["name_prefix"] + var_type if config["name_prefix"] else var_type
        else:
            var_name = config["name_prefix"] + stock_code
        
        existing = db.query(ContextVariable).filter(ContextVariable.name == var_name).first()
        
        if existing:
            # 更新类型和描述
            existing.type = config["type"]
            existing.symbol = stock_code
            existing.description = config["description"]
            existing.updated_at = datetime.now()
            db.commit()
            db.refresh(existing)
            results.append(existing)
        else:
            new_var = ContextVariable(
                name=var_name,
                type=config["type"],
                symbol=stock_code,
                data={},
                available=False,
                reason="等待查询",
                description=config["description"]
            )
            db.add(new_var)
            db.commit()
            db.refresh(new_var)
            results.append(new_var)
    
    logger.info(f"Auto-created {len(results)} variables for stock {stock_code}")
    return results


@router.delete("/variables/{name}")
async def delete_variable(name: str, db: Session = Depends(get_db)):
    """删除上下文变量"""
    variable = db.query(ContextVariable).filter(ContextVariable.name == name).first()
    if not variable:
        raise HTTPException(status_code=404, detail=f"Variable '{name}' not found")
    
    db.delete(variable)
    db.commit()
    logger.info(f"Deleted context variable: {name}")
    return {"message": f"Variable '{name}' deleted successfully"}


@router.delete("/variables")
async def delete_all_variables(db: Session = Depends(get_db)):
    """删除所有上下文变量"""
    db.query(ContextVariable).delete()
    db.commit()
    logger.info("Deleted all context variables")
    return {"message": "All context variables deleted successfully"}


@router.delete("/variables/stock/{stock_code}")
async def delete_stock_variables(stock_code: str, db: Session = Depends(get_db)):
    """删除指定股票的所有变量"""
    db.query(ContextVariable).filter(ContextVariable.symbol == stock_code).delete()
    db.commit()
    logger.info(f"Deleted all variables for stock {stock_code}")
    return {"message": f"All variables for stock {stock_code} deleted successfully"}
