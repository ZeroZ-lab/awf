import pytest
from typing import Dict, Any
from app.services.workflow_executor import WorkflowExecutor
import json

@pytest.fixture
def simple_workflow_config():
    return {
        "workflow_id": "test_workflow",
        "name": "Test Workflow",
        "description": "A workflow for testing",
        "version": "1.0",
        "parameters": {
            "max_length": 100,
            "style": "test"
        },
        "steps": [
            {
                "type": "llm",
                "description": "Test step 1",
                "model": "test-model",
                "prompt_template": "Process this: {input_text}",
                "temperature": 0.5,
                "max_tokens": 100
            }
        ]
    }

@pytest.fixture
def complex_workflow_config():
    return {
        "workflow_id": "test_complex_workflow",
        "name": "Test Complex Workflow",
        "description": "A complex workflow for testing",
        "version": "1.0",
        "parameters": {
            "max_length": 100,
            "style": "test",
            "threshold": 0.5
        },
        "steps": [
            {
                "type": "if",
                "description": "Conditional step",
                "condition": "len(input_text) > parameters['max_length']",
                "then": [
                    {
                        "type": "llm",
                        "model": "test-model",
                        "prompt_template": "Summarize: {input_text}",
                        "temperature": 0.3
                    }
                ],
                "else": [
                    {
                        "type": "llm",
                        "model": "test-model",
                        "prompt_template": "Process: {input_text}",
                        "temperature": 0.7
                    }
                ]
            },
            {
                "type": "llm",
                "description": "Final step",
                "model": "test-model",
                "prompt_template": "Enhance: {input_text}",
                "temperature": 0.5
            }
        ]
    }

@pytest.fixture
def mock_model(mocker):
    """创建模拟模型"""
    async def mock_generate_text(*args, **kwargs):
        return "Mocked response for: " + kwargs.get("prompt", "")
    
    model = mocker.AsyncMock()
    model.generate_text.side_effect = mock_generate_text
    return model

@pytest.fixture
def mock_models(mocker, mock_model):
    """创建模拟模型管理器"""
    models = mocker.Mock()
    models.get_model.return_value = mock_model
    mocker.patch("app.services.workflow_executor.models", models)
    return models

@pytest.mark.asyncio
async def test_workflow_initialization(simple_workflow_config):
    """测试工作流初始化"""
    executor = WorkflowExecutor(simple_workflow_config)
    assert executor.workflow_config == simple_workflow_config
    assert executor.context["workflow_id"] == "test_workflow"
    assert executor.context["steps_results"] == []
    assert executor.context["parameters"] is None

@pytest.mark.asyncio
async def test_simple_workflow_execution(simple_workflow_config, mock_models):
    """测试简单工作流执行"""
    executor = WorkflowExecutor(simple_workflow_config)
    result = await executor.execute(
        input_text="Test input",
        parameters={"max_length": 50}
    )
    
    assert result is not None
    assert isinstance(result, str)
    assert "Mocked response for: Process this: Test input" in result

@pytest.mark.asyncio
async def test_complex_workflow_execution(complex_workflow_config, mock_models):
    """测试复杂工作流执行"""
    executor = WorkflowExecutor(complex_workflow_config)
    result = await executor.execute(
        input_text="Short text",
        parameters={"max_length": 20, "style": "test"}
    )
    
    assert result is not None
    assert isinstance(result, str)
    assert "Mocked response for" in result

@pytest.mark.asyncio
async def test_workflow_parameter_merging(simple_workflow_config, mock_models):
    """测试参数合并"""
    executor = WorkflowExecutor(simple_workflow_config)
    
    # 使用自定义参数
    custom_params = {"max_length": 50, "style": "custom"}
    result = await executor.execute("Test input", custom_params)
    
    assert executor.context["parameters"] == {
        "max_length": 50,
        "style": "custom"
    }

@pytest.mark.asyncio
async def test_workflow_error_handling(simple_workflow_config, mock_models, mocker):
    """测试错误处理"""
    # 模拟模型生成错误
    async def mock_error(*args, **kwargs):
        raise Exception("Test error")
    
    mock_models.get_model.return_value.generate_text = mock_error
    
    executor = WorkflowExecutor(simple_workflow_config)
    
    with pytest.raises(Exception) as exc_info:
        await executor.execute("Test input")
    
    assert "Test error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_workflow_stream_execution(simple_workflow_config, mock_models):
    """测试流式执行"""
    executor = WorkflowExecutor(simple_workflow_config)
    
    async for event in executor.stream_execute("Test input"):
        assert isinstance(event, dict)
        assert "type" in event
        assert "timestamp" in event
        
        if event["type"] == "workflow_complete":
            assert "result" in event
            assert isinstance(event["result"], str)

@pytest.mark.asyncio
async def test_workflow_context_updates(simple_workflow_config, mock_models):
    """测试上下文更新"""
    executor = WorkflowExecutor(simple_workflow_config)
    await executor.execute("Test input")
    
    assert len(executor.context["steps_results"]) == 1
    assert executor.context["final_result"] is not None
    
    step_result = executor.context["steps_results"][0]
    assert step_result["step_type"] == "llm"
    assert step_result["input"] == "Test input"
    assert isinstance(step_result["output"], str)

@pytest.mark.asyncio
async def test_invalid_step_type(simple_workflow_config):
    """测试无效的步骤类型"""
    config = simple_workflow_config.copy()
    config["steps"][0]["type"] = "invalid_type"
    
    executor = WorkflowExecutor(config)
    
    with pytest.raises(ValueError) as exc_info:
        await executor.execute("Test input")
    
    assert "Unknown step type: invalid_type" in str(exc_info.value)

@pytest.mark.asyncio
async def test_missing_model_id(simple_workflow_config):
    """测试缺少模型ID"""
    config = simple_workflow_config.copy()
    del config["steps"][0]["model"]
    
    executor = WorkflowExecutor(config)
    
    with pytest.raises(ValueError) as exc_info:
        await executor.execute("Test input")
    
    assert "Model ID is required" in str(exc_info.value) 