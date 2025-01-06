import pytest
import asyncio
from app.services.parallel_executor import ParallelExecutor

@pytest.fixture
def mock_step_executor():
    async def executor(step, input_text):
        await asyncio.sleep(0.1)  # 模拟异步操作
        return f"Executed: {step['type']} with {input_text}"
    return executor

@pytest.fixture
def parallel_executor(mock_step_executor):
    return ParallelExecutor(mock_step_executor)

@pytest.mark.asyncio
async def test_parallel_execution(parallel_executor):
    """测试基本的并行执行功能"""
    step = {
        "type": "parallel",
        "steps": [
            {"type": "step1", "config": "test1"},
            {"type": "step2", "config": "test2"},
            {"type": "step3", "config": "test3"}
        ]
    }
    
    results = await parallel_executor.execute(step, "test_input", {})
    
    assert len(results) == 3
    assert all(isinstance(result, str) for result in results)
    assert "Executed: step1" in results[0]
    assert "Executed: step2" in results[1]
    assert "Executed: step3" in results[2]

@pytest.mark.asyncio
async def test_parallel_execution_empty_steps(parallel_executor):
    """测试空步骤列表的情况"""
    step = {
        "type": "parallel",
        "steps": []
    }
    
    with pytest.raises(ValueError) as exc_info:
        await parallel_executor.execute(step, "test_input", {})
    
    assert "No steps provided for parallel execution" in str(exc_info.value)

@pytest.mark.asyncio
async def test_parallel_execution_with_error(parallel_executor):
    """测试执行出错的情况"""
    async def error_executor(step, input_text):
        if step["type"] == "error_step":
            raise ValueError("Test error")
        return f"Executed: {step['type']} with {input_text}"
    
    executor = ParallelExecutor(error_executor)
    
    step = {
        "type": "parallel",
        "steps": [
            {"type": "step1", "config": "test1"},
            {"type": "error_step", "config": "test2"},
            {"type": "step3", "config": "test3"}
        ]
    }
    
    with pytest.raises(ValueError) as exc_info:
        await executor.execute(step, "test_input", {})
    
    assert "Test error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_parallel_execution_context_isolation(parallel_executor):
    """测试上下文隔离"""
    contexts = []
    
    async def context_tracking_executor(step, input_text):
        context = {"step": step["type"]}
        contexts.append(context)
        return f"Executed: {step['type']}"
    
    executor = ParallelExecutor(context_tracking_executor)
    
    step = {
        "type": "parallel",
        "steps": [
            {"type": "step1"},
            {"type": "step2"}
        ]
    }
    
    await executor.execute(step, "test_input", {})
    
    assert len(contexts) == 2
    assert contexts[0] != contexts[1]
    assert contexts[0]["step"] != contexts[1]["step"] 