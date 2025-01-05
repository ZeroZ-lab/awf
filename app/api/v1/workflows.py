from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Literal
from app.services.workflow_executor import WorkflowExecutor
from app.core.config import config
import time
import uuid
import asyncio
from enum import Enum
import json

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

# 存储运行中的工作流
running_workflows: Dict[str, Dict[str, Any]] = {}

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

class WorkflowRunRequest(BaseModel):
    input_text: str
    parameters: Optional[Dict[str, Any]] = None
    mode: Literal["sync", "async", "stream"] = "sync"  # 默认使用同步模式

class WorkflowResponse(BaseModel):
    execution_id: Optional[str] = None
    result: Optional[str] = None
    execution_time: Optional[float] = None
    status: str
    error: Optional[str] = None

class WorkflowInfo(BaseModel):
    workflow_id: str
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]]

class WorkflowStatusResponse(BaseModel):
    status: str
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    start_time: Optional[float] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None
    result: Optional[str] = None

class WorkflowResult(BaseModel):
    """工作流执行结果"""
    execution_id: str
    workflow_id: str
    status: str
    result: Optional[str] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None
    start_time: float

@router.get("/{workflow_id}", response_model=WorkflowInfo)
async def get_workflow(workflow_id: str):
    """获取工作流信息"""
    workflow = None
    for wf in config.get("workflows", []):
        if wf.get("workflow_id") == workflow_id:
            workflow = wf
            break
    
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found: {workflow_id}"
        )
    
    return WorkflowInfo(
        workflow_id=workflow["workflow_id"],
        name=workflow.get("name", "Unnamed Workflow"),
        description=workflow.get("description"),
        steps=workflow.get("steps", [])
    )

async def _execute_workflow(workflow_config: Dict[str, Any], 
                          input_text: str,
                          parameters: Optional[Dict[str, Any]],
                          execution_id: str):
    """在后台执行工作流"""
    try:
        running_workflows[execution_id]["status"] = WorkflowStatus.RUNNING
        executor = WorkflowExecutor(workflow_config)
        result = await executor.execute(input_text, parameters)
        
        execution_time = time.time() - running_workflows[execution_id]["start_time"]
        running_workflows[execution_id].update({
            "status": WorkflowStatus.COMPLETED,
            "result": result,
            "execution_time": execution_time,
            "current_step": len(workflow_config.get("steps", [])),
            "total_steps": len(workflow_config.get("steps", []))
        })
        return result
    except Exception as e:
        error_msg = str(e)
        running_workflows[execution_id].update({
            "status": WorkflowStatus.FAILED,
            "error": error_msg,
            "result": None
        })
        raise

async def stream_generator(workflow_config: Dict[str, Any],
                         input_text: str,
                         parameters: Optional[Dict[str, Any]]):
    """生成流式执行结果"""
    try:
        executor = WorkflowExecutor(workflow_config)
        async for step_result in executor.stream_execute(input_text, parameters):
            yield f"data: {json.dumps(step_result, ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    finally:
        yield "data: [DONE]\n\n"

@router.post("/{workflow_id}/run", response_model=WorkflowResponse)
async def run_workflow(
    workflow_id: str, 
    request: WorkflowRunRequest,
    background_tasks: BackgroundTasks
):
    """运行工作流
    
    支持三种执行模式：
    - sync: 同步执行，等待完成后返回结果
    - async: 异步执行，立即返回执行ID，通过status接口查询结果
    - stream: 流式执行，实时返回执行过程和结果
    """
    workflow_config = None
    for workflow in config.get("workflows", []):
        if workflow.get("workflow_id") == workflow_id:
            workflow_config = workflow
            break
    
    if not workflow_config:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found: {workflow_id}"
        )
    
    # 根据执行模式处理
    if request.mode == "stream":
        return StreamingResponse(
            stream_generator(
                workflow_config,
                request.input_text,
                request.parameters
            ),
            media_type="text/event-stream"
        )
    
    elif request.mode == "sync":
        try:
            start_time = time.time()
            executor = WorkflowExecutor(workflow_config)
            result = await executor.execute(
                request.input_text,
                request.parameters
            )
            execution_time = time.time() - start_time
            
            return WorkflowResponse(
                result=result,
                execution_time=execution_time,
                status=WorkflowStatus.COMPLETED
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    
    else:  # async mode
        execution_id = str(uuid.uuid4())
        total_steps = len(workflow_config.get("steps", []))
        
        # 初始化执行状态
        running_workflows[execution_id] = {
            "workflow_id": workflow_id,
            "status": WorkflowStatus.PENDING,
            "start_time": time.time(),
            "input_text": request.input_text,
            "parameters": request.parameters,
            "current_step": 0,
            "total_steps": total_steps,
            "result": None
        }
        
        try:
            # 在后台执行工作流
            background_tasks.add_task(
                _execute_workflow,
                workflow_config,
                request.input_text,
                request.parameters,
                execution_id
            )
            
            return WorkflowResponse(
                execution_id=execution_id,
                status=WorkflowStatus.PENDING,
                execution_time=0,
                result=None
            )
            
        except Exception as e:
            running_workflows[execution_id].update({
                "status": WorkflowStatus.FAILED,
                "error": str(e)
            })
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    execution_id: Optional[str] = Query(None, description="特定执行ID的状态，如果不提供则返回最新执行的状态")
):
    """获取工作流运行状态"""
    if execution_id:
        execution = running_workflows.get(execution_id)
        if not execution or execution["workflow_id"] != workflow_id:
            raise HTTPException(
                status_code=404,
                detail=f"Execution not found: {execution_id}"
            )
        latest_execution = execution
    else:
        # 查找最新的执行记录
        latest_execution = None
        latest_start_time = 0
        
        for exec_id, execution in running_workflows.items():
            if (execution["workflow_id"] == workflow_id and 
                execution["start_time"] > latest_start_time):
                latest_execution = execution
                latest_start_time = execution["start_time"]
        
        if not latest_execution:
            raise HTTPException(
                status_code=404,
                detail=f"No execution found for workflow: {workflow_id}"
            )
    
    execution_time = None
    if latest_execution["status"] in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
        execution_time = time.time() - latest_execution["start_time"]
    
    return WorkflowStatusResponse(
        status=latest_execution["status"],
        start_time=latest_execution["start_time"],
        execution_time=execution_time,
        error=latest_execution.get("error"),
        result=latest_execution.get("result"),
        current_step=latest_execution.get("current_step"),
        total_steps=latest_execution.get("total_steps")
    )

@router.post("/{workflow_id}/stop")
async def stop_workflow(
    workflow_id: str,
    execution_id: Optional[str] = Query(None, description="特定执行ID，如果不提供则停止该工作流的所有运行中实例")
):
    """停止工作流执行"""
    stopped = False
    
    if execution_id:
        execution = running_workflows.get(execution_id)
        if (execution and 
            execution["workflow_id"] == workflow_id and 
            execution["status"] == WorkflowStatus.RUNNING):
            execution["status"] = WorkflowStatus.STOPPED
            stopped = True
    else:
        for exec_id, execution in running_workflows.items():
            if (execution["workflow_id"] == workflow_id and 
                execution["status"] == WorkflowStatus.RUNNING):
                execution["status"] = WorkflowStatus.STOPPED
                stopped = True
    
    if not stopped:
        raise HTTPException(
            status_code=404,
            detail=f"No running execution found for workflow: {workflow_id}"
        )
    
    return {"status": "stopped"} 

@router.get("/{workflow_id}/result/{execution_id}", response_model=WorkflowResult)
async def get_workflow_result(workflow_id: str, execution_id: str):
    """获取异步执行的工作流结果
    
    Args:
        workflow_id: 工作流ID
        execution_id: 执行ID
    
    Returns:
        工作流执行结果，包括状态、结果、执行时间等
        
    Raises:
        HTTPException: 当执行记录不存在时
    """
    execution = running_workflows.get(execution_id)
    if not execution or execution["workflow_id"] != workflow_id:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {execution_id}"
        )
    
    execution_time = None
    if execution["status"] in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
        execution_time = time.time() - execution["start_time"]
    
    return WorkflowResult(
        execution_id=execution_id,
        workflow_id=workflow_id,
        status=execution["status"],
        result=execution.get("result"),
        execution_time=execution_time,
        error=execution.get("error"),
        start_time=execution["start_time"]
    ) 