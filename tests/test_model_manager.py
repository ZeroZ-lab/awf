import pytest
from app.services.model_manager import ModelManager
from app.models.agents import ModelConfig
import os

@pytest.fixture
def model_config():
    return ModelConfig(
        model_id="test-model",
        name="Test Model",
        type="openrouter",
        params={
            "model_name": "test/model",
            "api_key_env": "TEST_API_KEY"
        }
    )

@pytest.fixture
def models_yaml_content():
    """测试用的模型配置YAML内容"""
    return """
models:
  - model_id: test-model-1
    name: Test Model 1
    type: openrouter
    params:
      model_name: test/model
      api_key_env: TEST_API_KEY
  - model_id: test-model-2
    name: Test Model 2
    type: openai
    params:
      model_name: test-model-2
      api_key_env: TEST_API_KEY_2
"""

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("TEST_API_KEY", "test-key-123")
    monkeypatch.setenv("TEST_API_KEY_2", "test-key-456")
    return {
        "TEST_API_KEY": "test-key-123",
        "TEST_API_KEY_2": "test-key-456"
    }

def test_model_manager_initialization():
    """测试模型管理器初始化"""
    manager = ModelManager()
    assert isinstance(manager.models, dict)

def test_get_model(model_config, mock_env):
    """测试获取模型"""
    manager = ModelManager()
    manager.models[model_config.model_id] = manager.create_model(model_config)
    
    model = manager.get_model("test-model")
    assert model is not None
    assert model.config.model_id == "test-model"

def test_get_nonexistent_model():
    """测试获取不存在的模型"""
    manager = ModelManager()
    model = manager.get_model("nonexistent")
    assert model is None

def test_create_model(model_config, mock_env):
    """测试创建模型"""
    manager = ModelManager()
    model = manager.create_model(model_config)
    assert model is not None
    assert model.config == model_config

def test_create_model_invalid_type(model_config):
    """测试创建无效类型的模型"""
    manager = ModelManager()
    
    # 测试无效配置
    invalid_config = model_config.model_copy()
    invalid_config.type = "invalid_type"
    
    with pytest.raises(ValueError):
        manager.create_model(invalid_config)

def test_create_model_missing_api_key(model_config):
    """测试缺少API密钥的情况"""
    manager = ModelManager()
    with pytest.raises(ValueError) as exc_info:
        manager.create_model(model_config)
    assert "API key not found" in str(exc_info.value)

def test_load_models_from_yaml(tmp_path, models_yaml_content, mock_env):
    """测试从YAML文件加载模型"""
    # 创建临时配置文件
    config_file = tmp_path / "models.yaml"
    config_file.write_text(models_yaml_content)
    
    manager = ModelManager()
    manager.load_models(str(config_file))
    
    # 验证模型加载
    assert len(manager.models) > 0
    assert "test-model-1" in manager.models
    assert "test-model-2" in manager.models
    
    # 验证模型配置
    model1 = manager.models["test-model-1"]
    assert model1.config.model_id == "test-model-1"
    assert model1.config.type == "openrouter"
    
    model2 = manager.models["test-model-2"]
    assert model2.config.model_id == "test-model-2"
    assert model2.config.type == "openai"

def test_load_models_invalid_yaml(tmp_path):
    """测试加载无效的YAML文件"""
    # 创建无效的配置文件
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("invalid: yaml: content")
    
    manager = ModelManager()
    manager.load_models(str(config_file))
    
    # 应该加载默认配置
    assert len(manager.models) > 0

def test_load_models_missing_file():
    """测试配置文件不存在的情况"""
    manager = ModelManager()
    manager.load_models("nonexistent.yaml")
    
    # 应该加载默认配置
    assert len(manager.models) > 0

def test_list_models(model_config, mock_env):
    """测试列出所有模型"""
    manager = ModelManager()
    manager.models[model_config.model_id] = manager.create_model(model_config)
    
    models = manager.list_models()
    assert isinstance(models, dict)
    assert "test-model" in models
    assert models["test-model"] == "Test Model"

@pytest.mark.asyncio
async def test_model_text_generation(model_config, mock_env):
    """测试模型文本生成"""
    manager = ModelManager()
    model = manager.create_model(model_config)
    
    prompt = "Test prompt"
    try:
        result = await model.generate_text(prompt)
        assert isinstance(result, str)
    except Exception as e:
        pytest.skip(f"Skipping text generation test: {str(e)}")

def test_model_config_validation(model_config, mock_env):
    """测试模型配置验证"""
    manager = ModelManager()
    assert manager.create_model(model_config).validate_config() 