import pytest
import os
from app.models.agents import ModelConfig
from app.services.providers.openrouter_provider import OpenRouterProvider

@pytest.fixture
def test_config():
    return ModelConfig(
        model_id="test-openrouter",
        name="Test OpenRouter Model",
        type="openrouter",
        params={
            "api_key_env": "OPENROUTER_API_KEY",
            "model_name": "deepseek-chat",
            "api_base": "https://openrouter.ai/api/v1"
        }
    )

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("APP_URL", "http://test.com")
    monkeypatch.setenv("APP_NAME", "Test App")

@pytest.fixture
def provider(test_config, mock_env):
    return OpenRouterProvider(test_config)

def test_provider_initialization(provider):
    """测试 OpenRouter Provider 初始化"""
    assert provider.api_key == "test-key"
    assert provider.model_name == "deepseek-chat"
    assert provider.api_base == "https://openrouter.ai/api/v1"

def test_validate_config(provider):
    """测试配置验证"""
    assert provider.validate_config() is True

def test_missing_api_key(monkeypatch, test_config):
    """测试缺少 API Key 的情况"""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key not found"):
        OpenRouterProvider(test_config)

@pytest.mark.asyncio
async def test_generate_text(provider, mocker):
    """测试文本生成"""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Test response"
                }
            }
        ]
    }

    mock_client = mocker.AsyncMock()
    mock_client.post.return_value = mock_response
    
    mock_async_client = mocker.patch("httpx.AsyncClient")
    mock_async_client.return_value.__aenter__.return_value = mock_client

    result = await provider.generate_text("Test prompt")
    assert result == "Test response"

    # 验证请求参数
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert kwargs["json"]["model"] == "deepseek-chat"
    assert kwargs["json"]["messages"][0]["content"] == "Test prompt"

@pytest.mark.asyncio
async def test_generate_text_error(provider, mocker):
    """测试文本生成错误处理"""
    mock_response = mocker.Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad request"

    mock_client = mocker.AsyncMock()
    mock_client.post.return_value = mock_response
    
    mock_async_client = mocker.patch("httpx.AsyncClient")
    mock_async_client.return_value.__aenter__.return_value = mock_client

    with pytest.raises(Exception, match="OpenRouter API error: 400 - Bad request"):
        await provider.generate_text("Test prompt") 