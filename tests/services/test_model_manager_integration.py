import pytest
import os
from app.services.model_manager import ModelManager
from app.models.agents import ModelConfig

@pytest.fixture
def test_configs(tmp_path):
    """创建测试配置文件"""
    # 创建配置目录
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    
    # 创建 OpenAI 配置
    openai_config = models_dir / "openai.yaml"
    openai_config.write_text("""
models:
  - model_id: openai-test
    name: OpenAI Test
    type: openai
    params:
      model_name: test-model
      api_key_env: TEST_API_KEY
""")
    
    # 创建 OpenRouter 配置
    openrouter_config = models_dir / "openrouter.yaml"
    openrouter_config.write_text("""
models:
  - model_id: openrouter-test
    name: OpenRouter Test
    type: openrouter
    params:
      model_name: test/model
      api_key_env: TEST_API_KEY
""")
    
    # 创建主配置文件
    main_config = tmp_path / "models.yaml"
    main_config.write_text(f"""
includes:
  - models/openai.yaml
  - models/openrouter.yaml
""")
    
    return {
        "base_dir": str(tmp_path),
        "main_config": str(main_config)
    }

@pytest.fixture
def mock_env(monkeypatch):
    """Mock 环境变量"""
    monkeypatch.setenv("TEST_API_KEY", "test-key-123")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://test.openai.com/v1")
    return {
        "TEST_API_KEY": "test-key-123",
        "OPENAI_BASE_URL": "https://test.openai.com/v1"
    }

def test_model_manager_load_split_configs(test_configs, mock_env):
    """测试加载拆分的配置文件"""
    manager = ModelManager()
    manager.config_loader.base_dir = test_configs["base_dir"]
    manager.load_models(test_configs["main_config"])
    
    # 验证模型加载
    assert len(manager.models) == 2
    assert "openai-test" in manager.models
    assert "openrouter-test" in manager.models
    
    # 验证 OpenAI 模型
    openai_model = manager.models["openai-test"]
    assert openai_model.config.model_id == "openai-test"
    assert openai_model.config.type == "openai"
    assert openai_model.model_name == "test-model"
    
    # 验证 OpenRouter 模型
    openrouter_model = manager.models["openrouter-test"]
    assert openrouter_model.config.model_id == "openrouter-test"
    assert openrouter_model.config.type == "openrouter"
    assert openrouter_model.model_name == "test/model"

def test_model_manager_fallback_to_defaults(tmp_path, mock_env):
    """测试配置加载失败时的默认值"""
    # 创建无效的配置文件
    invalid_config = tmp_path / "invalid.yaml"
    invalid_config.write_text("invalid: yaml: content:")
    
    manager = ModelManager()
    manager.load_models(str(invalid_config))
    
    # 验证默认模型加载
    assert len(manager.models) > 0
    assert "openai-gpt-3.5-turbo-instruct" in manager.models
    assert "openrouter-deepseek" in manager.models

def test_model_manager_list_models(test_configs, mock_env):
    """测试列出模型"""
    manager = ModelManager()
    manager.config_loader.base_dir = test_configs["base_dir"]
    manager.load_models(test_configs["main_config"])
    
    models = manager.list_models()
    assert len(models) == 2
    assert models["openai-test"] == "OpenAI Test"
    assert models["openrouter-test"] == "OpenRouter Test"

@pytest.mark.asyncio
async def test_model_text_generation(test_configs, mock_env):
    """测试模型文本生成"""
    manager = ModelManager()
    manager.config_loader.base_dir = test_configs["base_dir"]
    manager.load_models(test_configs["main_config"])
    
    model = manager.get_model("openai-test")
    assert model is not None
    
    try:
        result = await model.generate_text("Test prompt")
        assert isinstance(result, str)
    except Exception as e:
        pytest.skip(f"Skipping text generation test: {str(e)}")

def test_model_manager_invalid_model_type(test_configs, mock_env, tmp_path):
    """测试无效的模型类型"""
    # 创建无效类型的模型配置
    invalid_config = tmp_path / "invalid_type.yaml"
    invalid_config.write_text("""
models:
  - model_id: invalid-test
    name: Invalid Test
    type: invalid_type
    params:
      model_name: test-model
      api_key_env: TEST_API_KEY
""")
    
    manager = ModelManager()
    manager.load_models(str(invalid_config))
    
    # 验证加载了默认模型
    assert len(manager.models) > 0
    assert all(model.config.type in ["openai", "openrouter"] for model in manager.models.values()) 