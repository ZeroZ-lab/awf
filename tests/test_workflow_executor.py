import pytest
from app.workflow_executor import WorkflowExecutor

def test_nested_workflow():
    executor = WorkflowExecutor()
    result = executor.run_workflow("nested_workflow", {"data": "test"})
    assert result is not None
    # 添加更多断言

def test_parallel_workflow():
    executor = WorkflowExecutor()
    result = executor.run_workflow("parallel_workflow", {"data": "test"})
    assert len(result) == 2  # 确保并行任务都执行了
    
def test_error_handling():
    executor = WorkflowExecutor()
    # 测试重试机制
    result = executor.run_workflow("error_handling_workflow", {"data": "test"})
    assert "fallback" in str(result) 