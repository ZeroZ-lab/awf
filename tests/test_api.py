import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.model_manager import models
from app.services.providers.base import BaseProvider
from typing import Dict, Any

client = TestClient(app)

class MockProvider(BaseProvider):
    async def generate_text(self, prompt: str, **kwargs) -> str:
        return f"Mock response for: {prompt}"
    
    def validate_config(self) -> bool:
        return True

@pytest.fixture
def mock_workflow_config():
    return {
        "workflow_id": "test-workflow",
        "name": "Test Workflow",
        "description": "A workflow for testing",
        "parameters": {
            "max_length": 100,
            "style": "test"
        },
        "steps": [
            {
                "type": "llm",
                "description": "Test step",
                "model": "test-model",
                "prompt_template": "Process this: {input_text}",
                "temperature": 0.5,
                "max_tokens": 100
            }
        ]
    }

@pytest.fixture
def mock_model():
    return MockProvider({
        "model_id": "test-model",
        "name": "Test Model",
        "type": "test",
        "params": {}
    })

@pytest.fixture
def mock_config(mocker, mock_workflow_config, mock_model):
    mocker.patch("app.api.v1.workflows.get_workflow_config", return_value=mock_workflow_config)
    models.register_model("test-model", mock_model)

def test_run_workflow(mock_config):
    """测试运行工作流"""
    response = client.post(
        "/workflows/test-workflow/run",
        json={
            "workflow_id": "test-workflow",
            "input_text": "Test input",
            "parameters": {"max_length": 50}
        }
    )
    assert response.status_code == 200
    assert "result" in response.json()

def test_run_workflow_stream(mock_config):
    """测试流式运行工作流"""
    response = client.post(
        "/workflows/test-workflow/run/stream",
        json={
            "workflow_id": "test-workflow",
            "input_text": "Test input",
            "parameters": {"max_length": 50}
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"

def test_nonexistent_workflow():
    """测试不存在的工作流"""
    response = client.post(
        "/workflows/nonexistent/run",
        json={
            "workflow_id": "nonexistent",
            "input_text": "Test input"
        }
    )
    assert response.status_code == 404
    assert "Workflow not found" in response.json()["detail"]

def test_invalid_workflow_request(mock_config):
    """测试无效的请求"""
    response = client.post(
        "/workflows/test-workflow/run",
        json={
            "workflow_id": "test-workflow"
            # 缺少必需的 input_text 字段
        }
    )
    assert response.status_code == 422

def test_workflow_error_handling(mock_config, mocker):
    """测试错误处理"""
    # 模拟执行错误
    mocker.patch(
        "app.services.workflow_executor.WorkflowExecutor.execute",
        side_effect=Exception("Test error")
    )
    
    response = client.post(
        "/workflows/test-workflow/run",
        json={
            "workflow_id": "test-workflow",
            "input_text": "Test input"
        }
    )
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]

def test_workflow_parameter_validation(mock_config):
    """测试参数验证"""
    response = client.post(
        "/workflows/test-workflow/run",
        json={
            "workflow_id": "test-workflow",
            "input_text": "Test input",
            "parameters": {
                "max_length": "invalid"  # 应该是整数
            }
        }
    )
    assert response.status_code == 200  # 参数验证在工作流执行时处理 