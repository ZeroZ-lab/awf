import pytest
from fastapi.testclient import TestClient
from app.main import app
import json
from typing import Dict, Any
from app.services.model_manager import models
from app.models.agents import ModelConfig
from app.services.providers.base import BaseProvider

class MockProvider(BaseProvider):
    async def generate_text(self, prompt: str, **kwargs) -> str:
        return f"Mocked response for: {prompt}"

    def validate_config(self) -> bool:
        return True

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_workflow_config():
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
                "description": "Test step",
                "model": "test-model",
                "prompt_template": "Process this: {input_text}",
                "temperature": 0.5
            }
        ]
    }

@pytest.fixture
def mock_model():
    config = ModelConfig(
        model_id="test-model",
        name="Test Model",
        type="test",
        params={}
    )
    return MockProvider(config)

@pytest.fixture
def mock_config(mocker, mock_workflow_config, mock_model):
    config = {
        "workflows": [mock_workflow_config]
    }
    mocker.patch("app.api.v1.workflows.config", config)
    # Mock the model manager
    mocker.patch.object(models, "get_model", return_value=mock_model)
    return config

def test_get_workflow(client, mock_config):
    """测试获取工作流信息"""
    response = client.get("/api/v1/workflows/test_workflow")
    assert response.status_code == 200
    
    data = response.json()
    assert data["workflow_id"] == "test_workflow"
    assert data["name"] == "Test Workflow"
    assert len(data["steps"]) == 1

def test_get_nonexistent_workflow(client, mock_config):
    """测试获取不存在的工作流"""
    response = client.get("/api/v1/workflows/nonexistent")
    assert response.status_code == 404

def test_run_workflow_sync(client, mock_config):
    """测试同步执行工作流"""
    response = client.post(
        "/api/v1/workflows/test_workflow/run",
        json={
            "input_text": "Test input",
            "parameters": {"max_length": 50},
            "mode": "sync"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "Mocked response for: Process this: Test input" in data["result"]

def test_run_workflow_async(client, mock_config):
    """测试异步执行工作流"""
    response = client.post(
        "/api/v1/workflows/test_workflow/run",
        json={
            "input_text": "Test input",
            "parameters": {"max_length": 50},
            "mode": "async"
        }
    )
    
    assert response.status_code == 202  # Accepted
    data = response.json()
    assert data["status"] == "pending"
    assert "execution_id" in data

def test_run_workflow_stream(client, mock_config):
    """测试流式执行工作流"""
    with client.stream(
        "POST",
        "/api/v1/workflows/test_workflow/run",
        json={
            "input_text": "Test input",
            "parameters": {"max_length": 50},
            "mode": "stream"
        }
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
        
        # 读取流式响应
        events = []
        for line in response.iter_lines():
            if line:
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                if line.startswith("data: "):
                    event = json.loads(line.replace("data: ", ""))
                    events.append(event)
        
        assert any(event.get("type") == "workflow_start" for event in events)
        assert any(event.get("type") == "complete" for event in events)

def test_get_workflow_status(client, mock_config):
    """测试获取工作流状态"""
    # 首先启动一个异步工作流
    response = client.post(
        "/api/v1/workflows/test_workflow/run",
        json={
            "input_text": "Test input",
            "mode": "async"
        }
    )
    
    assert response.status_code == 202  # Accepted
    execution_id = response.json()["execution_id"]
    
    # 然后获取状态
    response = client.get(f"/api/v1/workflows/test_workflow/status/{execution_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "current_step" in data
    assert "total_steps" in data

def test_invalid_workflow_request(client, mock_config):
    """测试无效的工作流请求"""
    response = client.post(
        "/api/v1/workflows/test_workflow/run",
        json={
            "parameters": {"max_length": 50}  # 缺少必需的 input_text
        }
    )
    
    assert response.status_code == 422  # Unprocessable Entity

def test_workflow_error_handling(client, mock_config, mocker):
    """测试工作流错误处理"""
    # 模拟执行错误
    error_model = MockProvider(ModelConfig(
        model_id="test-model",
        name="Test Model",
        type="test",
        params={}
    ))
    
    async def mock_generate_text(*args, **kwargs):
        raise Exception("Test error")
    
    error_model.generate_text = mock_generate_text
    mocker.patch.object(models, "get_model", return_value=error_model)
    
    response = client.post(
        "/api/v1/workflows/test_workflow/run",
        json={
            "input_text": "Test input",
            "mode": "sync"
        }
    )
    
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]

def test_workflow_parameter_validation(client, mock_config):
    """测试工作流参数验证"""
    response = client.post(
        "/api/v1/workflows/test_workflow/run",
        json={
            "input_text": "Test input",
            "parameters": {
                "max_length": "invalid"  # 应该是整数
            }
        }
    )
    
    assert response.status_code == 422  # Unprocessable Entity 