"""
Tools API Router - 工具配置和管理 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from app.services.llm.tools import (
    get_registry,
    get_all_tools_json,
    get_enabled_tools_json,
    DEFAULT_CATEGORIES,
    ToolDefinition,
    ToolCategory,
)
from app.services.logging_manager import get_logger

logger = get_logger("tools_router")

router = APIRouter(prefix="/api/tools", tags=["tools"])


class ToolEnabledRequest(BaseModel):
    """启用工具请求"""
    tool_ids: List[str]


class ToolTestRequest(BaseModel):
    """工具测试请求"""
    tool_id: str
    params: Dict[str, Any] = {}


class ToolCategoryRequest(BaseModel):
    """分类请求"""
    id: str
    name: str
    description: str
    color: str
    icon: str
    order: int = 0


@router.get("")
async def get_all_tools():
    """获取所有工具列表"""
    try:
        tools = get_all_tools_json()
        categories = [
            {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "color": cat.color,
                "icon": cat.icon,
                "order": cat.order,
            }
            for cat in DEFAULT_CATEGORIES
        ]
        
        registry = get_registry()
        enabled_ids = registry.get_enabled_tool_ids()
        
        for tool in tools:
            tool["is_enabled"] = tool["tool_id"] in enabled_ids
        
        return {
            "tools": tools,
            "categories": categories,
            "total": len(tools),
        }
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enabled")
async def get_enabled_tools():
    """获取启用的工具列表"""
    try:
        tools = get_enabled_tools_json()
        return {
            "tools": tools,
            "total": len(tools),
        }
    except Exception as e:
        logger.error(f"Error getting enabled tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enabled")
async def save_enabled_tools(request: ToolEnabledRequest):
    """保存启用的工具配置"""
    try:
        registry = get_registry()
        registry.set_enabled_tool_ids(request.tool_ids)
        
        logger.info(f"Saved enabled tools: {request.tool_ids}")
        
        return {
            "success": True,
            "message": f"已保存 {len(request.tool_ids)} 个启用的工具",
            "enabled_count": len(request.tool_ids),
        }
    except Exception as e:
        logger.error(f"Error saving enabled tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tool_id}")
async def get_tool_detail(tool_id: str):
    """获取工具详情"""
    try:
        registry = get_registry()
        tool = registry.get_tool(tool_id)
        
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")
        
        tool_dict = tool.to_dict()
        tool_dict["is_enabled"] = registry.is_tool_enabled(tool_id)
        
        category = registry.get_category(tool.category)
        if category:
            tool_dict["category_info"] = {
                "id": category.id,
                "name": category.name,
                "color": category.color,
                "icon": category.icon,
            }
        
        return tool_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_tool_in_thread(tool_func, params):
    """在独立线程中运行工具（带独立事件循环）"""
    import asyncio
    
    async def run_async():
        try:
            return await tool_func.ainvoke(params)
        except Exception:
            pass
        try:
            return tool_func.invoke(params)
        except Exception as e:
            return f"Error: {str(e)}"
    
    return asyncio.run(run_async())


@router.post("/test")
async def test_tool(request: ToolTestRequest):
    """测试工具执行"""
    try:
        import asyncio
        import concurrent.futures
        
        registry = get_registry()
        
        tool = registry.get_tool(request.tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {request.tool_id} not found")
        
        tool_func = registry.get_tool_function(request.tool_id)
        
        if tool_func:
            try:
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = await loop.run_in_executor(
                        pool, 
                        lambda: run_tool_in_thread(tool_func, request.params)
                    )
                return {
                    "success": True,
                    "tool_id": request.tool_id,
                    "result": str(result) if result else "No result",
                }
            except Exception as e:
                return {
                    "success": False,
                    "tool_id": request.tool_id,
                    "error": str(e),
                }
        
        from app.services.llm.tools.stock_tools import STOCK_TOOLS
        for tool_obj in STOCK_TOOLS:
            if tool_obj.name == request.tool_id:
                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        concurrent.futures.ThreadPoolExecutor(),
                        lambda: run_tool_in_thread(tool_obj, request.params)
                    )
                    return {
                        "success": True,
                        "tool_id": request.tool_id,
                        "result": str(result) if result else "No result",
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "tool_id": request.tool_id,
                        "error": str(e),
                    }
        
        raise HTTPException(status_code=404, detail=f"Tool function {request.tool_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """获取所有分类"""
    try:
        categories = [
            {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "color": cat.color,
                "icon": cat.icon,
                "order": cat.order,
            }
            for cat in DEFAULT_CATEGORIES
        ]
        
        registry = get_registry()
        all_tools = registry.get_all_tools()
        
        for cat in categories:
            cat["tool_count"] = len([t for t in all_tools if t.category == cat["id"]])
        
        return {
            "categories": sorted(categories, key=lambda x: x["order"]),
        }
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categories")
async def create_category(request: ToolCategoryRequest):
    """创建新分类"""
    try:
        registry = get_registry()
        
        new_category = ToolCategory(
            id=request.id,
            name=request.name,
            description=request.description,
            color=request.color,
            icon=request.icon,
            order=request.order,
        )
        
        registry.register_category(new_category)
        
        return {
            "success": True,
            "message": f"分类 {request.name} 创建成功",
            "category": {
                "id": new_category.id,
                "name": new_category.name,
                "description": new_category.description,
                "color": new_category.color,
                "icon": new_category.icon,
                "order": new_category.order,
            },
        }
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_tools():
    """刷新工具列表"""
    try:
        registry = get_registry()
        registry.refresh_tools()
        
        return {
            "success": True,
            "message": "工具列表已刷新",
        }
    except Exception as e:
        logger.error(f"Error refreshing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ToolEnabledRequest(BaseModel):
    enabled: bool


@router.put("/{tool_id}")
async def update_tool(tool_id: str, request: ToolEnabledRequest):
    """更新工具启用状态"""
    try:
        registry = get_registry()
        registry.set_tool_enabled(tool_id, request.enabled)
        
        return {
            "success": True,
            "message": f"工具 {tool_id} 已{'启用' if request.enabled else '禁用'}",
            "tool_id": tool_id,
            "is_enabled": request.enabled,
        }
    except Exception as e:
        logger.error(f"Error updating tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))
