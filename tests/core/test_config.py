import pytest
import os
from app.core.config import load_config, validate_config

@pytest.fixture
def mock_config_files(tmp_path):
    """创建测试配置文件"""
    # 创建工作流配置
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()
    
    workflow_file = workflows_dir / "test_workflow.yaml"
    workflow_file.write_text("""
workflow_id: test_workflow
name: Test Workflow
steps:
  - type: llm
    model: test-model
    prompt_template: "Test prompt: {input_text}"
""")
    
    # 创建模型配置
    models_file = tmp_path / "models.yaml"
    models_file.write_text("""
models:
  - model_id: test-model
    name: Test Model
    type: test
    params:
      api_key_env: TEST_API_KEY
""")
    
    # 创建工具配置
    tools_file = tmp_path / "tools.yaml"
    tools_file.write_text("""
tools:
  - name: TestTool
    description: A test tool
    class_name: TestTool
    module: app.tools.test
""")
    
    return {
        "workflows_dir": str(workflows_dir),
        "models_file": str(models_file),
        "tools_file": str(tools_file)
    }

def test_load_config(mock_config_files):
    """测试配置加载"""
    config = load_config(
        workflows_dir=mock_config_files["workflows_dir"],
        models_file=mock_config_files["models_file"],
        tools_file=mock_config_files["tools_file"]
    )
    
    assert len(config["workflows"]) == 1
    assert config["workflows"][0]["workflow_id"] == "test_workflow"
    
    assert len(config["models"]) == 1
    assert config["models"][0]["model_id"] == "test-model"
    
    assert len(config["tools"]) == 1
    assert config["tools"][0]["name"] == "TestTool"

def test_validate_config(mock_config_files):
    """测试配置验证"""
    config = load_config(
        workflows_dir=mock_config_files["workflows_dir"],
        models_file=mock_config_files["models_file"],
        tools_file=mock_config_files["tools_file"]
    )
    
    # 验证工作流配置
    workflow = config["workflows"][0]
    assert "workflow_id" in workflow
    assert "name" in workflow
    assert "steps" in workflow
    assert len(workflow["steps"]) > 0
    
    # 验证模型配置
    model = config["models"][0]
    assert "model_id" in model
    assert "name" in model
    assert "type" in model
    assert "params" in model
    
    # 验证工具配置
    tool = config["tools"][0]
    assert "name" in tool
    assert "description" in tool
    assert "class_name" in tool
    assert "module" in tool

def test_invalid_workflow_config(mock_config_files, tmp_path):
    """测试无效的工作流配置"""
    invalid_workflow = tmp_path / "workflows" / "invalid.yaml"
    invalid_workflow.write_text("""
workflow_id: invalid
# 缺少必需的字段
""")
    
    with pytest.raises(ValueError, match="Invalid workflow configuration"):
        load_config(
            workflows_dir=str(tmp_path / "workflows"),
            models_file=mock_config_files["models_file"],
            tools_file=mock_config_files["tools_file"]
        )

def test_invalid_model_config(mock_config_files, tmp_path):
    """测试无效的模型配置"""
    invalid_models = tmp_path / "models.yaml"
    invalid_models.write_text("""
models:
  - model_id: invalid
    # 缺少必需的字段
""")
    
    with pytest.raises(ValueError, match="Invalid model configuration"):
        load_config(
            workflows_dir=mock_config_files["workflows_dir"],
            models_file=str(invalid_models),
            tools_file=mock_config_files["tools_file"]
        )

def test_invalid_tool_config(mock_config_files, tmp_path):
    """测试无效的工具配置"""
    invalid_tools = tmp_path / "tools.yaml"
    invalid_tools.write_text("""
tools:
  - name: invalid
    # 缺少必需的字段
""")
    
    with pytest.raises(ValueError, match="Invalid tool configuration"):
        load_config(
            workflows_dir=mock_config_files["workflows_dir"],
            models_file=mock_config_files["models_file"],
            tools_file=str(invalid_tools)
        ) 