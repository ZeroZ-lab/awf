from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from pydantic import BaseModel
from app.services.workflow_executor import WorkflowExecutor
from app.core.monitoring import WorkflowMonitoring
from app.core.config import config
import time

router = APIRouter()

class ExecutionRequest(BaseModel):
    input_text: str
    workflow_id: str

class ExecutionResponse(BaseModel):
    result: str
    execution_time: float
    status: str

@router.post("/execute", response_model=ExecutionResponse)
async def execute_task(request: ExecutionRequest):
    start_time = time.time()
    status = "error"
    result = ""
    
    try:
        # 获取 workflow 配置
        workflow_config = None
        for workflow in config.get("workflows", []):
            if workflow["workflow_id"] == request.workflow_id:
                workflow_config = workflow
                break
                
        if not workflow_config:
            raise HTTPException(
                status_code=404, 
                detail=f"Workflow not found: {request.workflow_id}"
            )
            
        # 执行 workflow
        executor = WorkflowExecutor(workflow_config)
        result = await executor.execute(request.input_text)
        status = "success"
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 记录监控指标
        WorkflowMonitoring.record_execution(
            request.workflow_id,
            start_time,
            status
        )
    
    return ExecutionResponse(
        result=result,
        execution_time=time.time() - start_time,
        status=status
    ) 