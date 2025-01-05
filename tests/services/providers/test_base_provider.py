import pytest
from app.models.agents import ModelConfig
from app.services.providers.base import BaseProvider

class TestProvider(BaseProvider):
    async def generate_text(self, prompt: str, **kwargs) -> str:
        return f"Test response: {prompt}"

    def validate_config(self) -> bool:
        return True

@pytest.fixture
def test_config():
    return ModelConfig(
        model_id="test-model",
        name="Test Model",
        type="test",
        params={"key": "value"}
    )

@pytest.fixture
def provider(test_config):
    return TestProvider(test_config)

def test_provider_initialization(provider, test_config):
    """测试 Provider 初始化"""
    assert provider.config == test_config
    assert provider.config.model_id == "test-model"
    assert provider.config.params == {"key": "value"}

@pytest.mark.asyncio
async def test_generate_text(provider):
    """测试文本生成"""
    prompt = "Hello, world!"
    result = await provider.generate_text(prompt)
    assert result == "Test response: Hello, world!"

def test_validate_config(provider):
    """测试配置验证"""
    assert provider.validate_config() is True 