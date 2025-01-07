from typing import Dict, Any
from fastapi import HTTPException, status
from app.services.tool_manager import tools
from app.services.model_manager import models
from app.tools.base import BaseTool
from app.services.providers.base import BaseProvider

def get_tools() -> Dict[str, BaseTool]:
    """获取所有可用的工具"""
    if not tools.tools:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tool manager not initialized"
        )
    return tools.tools

def get_models() -> Dict[str, BaseProvider]:
    """获取所有可用的模型"""
    if not models.models:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model manager not initialized"
        )
    return models.models

def get_tool(tool_id: str) -> BaseTool:
    """获取指定ID的工具"""
    tools_dict = get_tools()
    tool = tools_dict.get(tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}"
        )
    return tool

def get_model(model_id: str) -> BaseProvider:
    """获取指定ID的模型"""
    models_dict = get_models()
    model = models_dict.get(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found 1: {model_id}"
        )
    return model 