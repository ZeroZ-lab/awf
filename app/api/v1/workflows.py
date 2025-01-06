from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from typing import Dict, Any, Optional
from app.services.workflow_executor import WorkflowExecutor
from app.core.config import load_config, DEFAULT_WORKFLOWS_DIR, DEFAULT_MODELS_FILE, DEFAULT_TOOLS_FILE
import logging
import json
import asyncio
from datetime import datetime
import os

router = APIRouter()
logger = logging.getLogger(__name__)

class WorkflowRequest(BaseModel):
    """工作流请求模型"""
    workflow_id: str
    input_text: str
    parameters: Optional[Dict[str, Any]] = None
    
    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v):
        """验证参数"""
        if v is None:
            return {}
        return v

def get_workflow_config(workflow_id: str) -> Dict[str, Any]:
    """获取工作流配置"""
    try:
        # 先检查工作流文件是否存在
        workflow_path = os.path.join(DEFAULT_WORKFLOWS_DIR, f"{workflow_id}.yaml")
        if not os.path.exists(workflow_path):
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
            
        config = load_config(DEFAULT_WORKFLOWS_DIR, DEFAULT_MODELS_FILE, DEFAULT_TOOLS_FILE)
        if not config["workflows"]:
            raise HTTPException(status_code=404, detail="No workflows found")
            
        workflows = {w["workflow_id"]: w for w in config["workflows"]}
        if workflow_id not in workflows:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
        
        return workflows[workflow_id]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str, request: WorkflowRequest):
    """
    运行工作流
    """
    workflow_config = get_workflow_config(workflow_id)
    executor = WorkflowExecutor(workflow_config)
    
    try:
        result = await executor.execute(request.input_text, request.parameters)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/{workflow_id}/run/stream")
async def run_workflow_stream(workflow_id: str, request: WorkflowRequest):
    """
    流式运行工作流
    """
    workflow_config = get_workflow_config(workflow_id)
    executor = WorkflowExecutor(workflow_config)
    
    async def generate():
        try:
            async for event in executor.stream_execute(request.input_text, request.parameters):
                if event["type"] == "complete":
                    yield f"data: {json.dumps(event)}\n\n"
                    break
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            error_event = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream"
        }
    ) 