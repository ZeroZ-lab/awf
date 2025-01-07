from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from typing import Dict, Any, Optional, Union
from app.services.workflow_executor import WorkflowExecutor
from app.core.config import load_config, DEFAULT_WORKFLOWS_DIR, DEFAULT_MODELS_FILE, DEFAULT_TOOLS_FILE
import logging
import json
from datetime import datetime
import os

router = APIRouter()
logger = logging.getLogger(__name__)

class WorkflowRequest(BaseModel):
    """工作流请求模型"""
    input_text: str
    parameters: Optional[Dict[str, Any]] = None
    stream: Optional[bool] = False
    async_: Optional[bool] = False
    
    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v):
        """验证参数"""
        if v is None:
            return {}
        return v

class WorkflowResponse(BaseModel):
    """工作流响应模型"""
    task_id: Optional[str] = None
    result: Optional[str] = None
    status: str
    message: Optional[str] = None

# 存储异步任务的结果
workflow_tasks: Dict[str, Dict[str, Any]] = {}

async def execute_workflow_task(task_id: str, workflow_config: Dict[str, Any], input_text: str, parameters: Dict[str, Any]):
    """在后台执行工作流任务"""
    try:
        executor = WorkflowExecutor(workflow_config)
        result = await executor.execute(input_text, parameters)
        workflow_tasks[task_id] = {
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing workflow task {task_id}: {str(e)}")
        workflow_tasks[task_id] = {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

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

@router.post(
    "/workflows/{workflow_id}/run",
    response_model=None,
    responses={
        200: {
            "description": "成功执行工作流",
            "content": {
                "application/json": {
                    "example": {
                        "task_id": "workflow_123_1234567890",
                        "result": "执行结果",
                        "status": "completed",
                        "message": "执行成功"
                    }
                },
                "text/event-stream": {
                    "example": 'data: {"type": "step_start", "step": 1, "total_steps": 3}\n\n'
                }
            }
        }
    }
)
async def run_workflow(
    workflow_id: str,
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
):
    """
    运行工作流
    
    支持三种模式：
    1. 同步执行（默认）：返回 WorkflowResponse
    2. 流式执行（stream=True）：返回 StreamingResponse
    3. 异步执行（async=True）：返回 WorkflowResponse，包含 task_id
    
    Returns:
        Union[WorkflowResponse, StreamingResponse]: 根据执行模式返回不同类型的响应
    """
    workflow_config = get_workflow_config(workflow_id)
    executor = WorkflowExecutor(workflow_config)
    
    # 如果请求流式响应，返回 StreamingResponse
    if request.stream:
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
                "X-Accel-Buffering": "no"
            }
        )
        
    # 如果请求异步执行，创建后台任务
    if request.async_:
        task_id = f"{workflow_id}_{datetime.now().timestamp()}"
        workflow_tasks[task_id] = {"status": "pending"}
        
        background_tasks.add_task(
            execute_workflow_task,
            task_id,
            workflow_config,
            request.input_text,
            request.parameters
        )
        
        return WorkflowResponse(
            task_id=task_id,
            status="pending",
            message="Task started"
        )
    
    # 同步执行
    try:
        result = await executor.execute(request.input_text, request.parameters)
        return WorkflowResponse(
            result=result,
            status="completed"
        )
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/tasks/{task_id}", response_model=WorkflowResponse)
async def get_task_status(task_id: str) -> WorkflowResponse:
    """获取异步任务的状态和结果"""
    task = workflow_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task["status"] == "completed":
        return WorkflowResponse(
            task_id=task_id,
            result=task["result"],
            status="completed"
        )
    elif task["status"] == "failed":
        return WorkflowResponse(
            task_id=task_id,
            status="failed",
            message=task["error"]
        )
    else:
        return WorkflowResponse(
            task_id=task_id,
            status="pending",
            message="Task is still running"
        ) 