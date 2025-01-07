import pytest
import os
from app.core.config_loader import ConfigLoader

@pytest.fixture
def config_loader():
    return ConfigLoader()

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
        "main_config": str(main_config),
        "openai_config": str(openai_config),
        "openrouter_config": str(openrouter_config)
    }

def test_resolve_path(config_loader):
    """测试路径解析"""
    # 测试相对路径
    relative_path = "models/test.yaml"
    resolved_path = config_loader._resolve_path(relative_path)
    expected_path = os.path.normpath(os.path.join(config_loader.base_dir, relative_path))
    assert resolved_path == expected_path
    
    # 测试绝对路径
    absolute_path = os.path.abspath("/absolute/path/test.yaml")
    resolved_path = config_loader._resolve_path(absolute_path)
    assert resolved_path == os.path.normpath(absolute_path)

def test_load_yaml(config_loader, test_configs):
    """测试 YAML 文件加载"""
    # 测试加载有效的 YAML
    config = config_loader._load_yaml(test_configs["openai_config"])
    assert config is not None
    assert "models" in config
    assert len(config["models"]) == 1
    assert config["models"][0]["model_id"] == "openai-test"
    
    # 测试加载不存在的文件
    config = config_loader._load_yaml("nonexistent.yaml")
    assert config is None

def test_merge_configs(config_loader):
    """测试配置合并"""
    configs = [
        {
            "models": [
                {"id": "model1"},
                {"id": "model2"}
            ]
        },
        {
            "models": [
                {"id": "model3"}
            ],
            "tools": [
                {"name": "tool1"}
            ]
        },
        None  # 测试空配置的处理
    ]
    
    merged = config_loader._merge_configs(configs)
    assert "models" in merged
    assert len(merged["models"]) == 3
    assert "tools" in merged
    assert len(merged["tools"]) == 1
    
    # 测试空列表
    assert config_loader._merge_configs([]) == {"models": [], "tools": []}

def test_load_config_with_includes(config_loader, test_configs):
    """测试带 includes 的配置加载"""
    # 设置基础目录
    config_loader.base_dir = test_configs["base_dir"]
    
    # 加载主配置
    config = config_loader.load_config(test_configs["main_config"])
    
    # 验证配置加载和合并
    assert config is not None
    assert "models" in config
    assert len(config["models"]) == 2
    
    # 验证具体模型
    model_ids = {model["model_id"] for model in config["models"]}
    assert "openai-test" in model_ids
    assert "openrouter-test" in model_ids

def test_load_config_without_includes(config_loader, test_configs):
    """测试不带 includes 的配置加载"""
    config = config_loader.load_config(test_configs["openai_config"])
    assert config is not None
    assert "models" in config
    assert len(config["models"]) == 1
    assert config["models"][0]["model_id"] == "openai-test"

def test_load_invalid_config(config_loader, tmp_path):
    """测试加载无效配置"""
    # 创建无效的 YAML 文件
    invalid_config = tmp_path / "invalid.yaml"
    invalid_config.write_text("invalid: yaml: content:")
    
    config = config_loader.load_config(str(invalid_config))
    assert config == {} 