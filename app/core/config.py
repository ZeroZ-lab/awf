import yaml
import os
import logging
from typing import Dict, Any, List
from app.models.tools import ToolConfig
from app.models.agents import AgentConfig
from app.models.workflows import WorkflowConfig

logger = logging.getLogger(__name__)

def validate_workflow(workflow: Dict[str, Any]) -> bool:
    """验证工作流配置"""
    required_fields = ["workflow_id", "name", "steps"]
    return all(field in workflow for field in required_fields)

def validate_model(model: Dict[str, Any]) -> bool:
    """验证模型配置"""
    required_fields = ["model_id", "name", "type", "params"]
    return all(field in model for field in required_fields)

def validate_tool(tool: Dict[str, Any]) -> bool:
    """验证工具配置"""
    required_fields = ["name", "description", "class_name", "module"]
    return all(field in tool for field in required_fields)

def validate_config(config: Dict[str, Any]) -> List[str]:
    if not config:
        return ["配置为空"]
        
    errors = []
    
    # 验证工具配置
    tool_names = set()
    for tool in config.get("tools", []):
        if not validate_tool(tool):
            errors.append(f"工具配置无效: {tool.get('name', 'unknown')}")
        if tool["name"] in tool_names:
            errors.append(f"重复的工具名称: {tool['name']}")
        tool_names.add(tool["name"])
    
    # 验证模型配置
    for model in config.get("models", []):
        if not validate_model(model):
            errors.append(f"模型配置无效: {model.get('model_id', 'unknown')}")
    
    # 验证工作流配置
    for workflow in config.get("workflows", []):
        if not validate_workflow(workflow):
            errors.append(f"工作流配置无效: {workflow.get('workflow_id', 'unknown')}")
    
    return errors

def load_config(workflows_dir: str, models_file: str, tools_file: str) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        workflows_dir: 工作流配置目录
        models_file: 模型配置文件路径
        tools_file: 工具配置文件路径
        
    Returns:
        Dict[str, Any]: 配置字典
        
    Raises:
        ValueError: 如果配置无效
    """
    config = {
        "workflows": [],
        "models": [],
        "tools": []
    }
    
    # 加载工作流配置
    if not os.path.exists(workflows_dir):
        logger.warning(f"Workflows directory not found: {workflows_dir}")
        return config
        
    workflow_files = [f for f in os.listdir(workflows_dir) if f.endswith(".yaml")]
    if not workflow_files:
        logger.warning(f"No workflow files found in {workflows_dir}")
        return config
        
    has_invalid_workflow = False
    for filename in workflow_files:
        try:
            with open(os.path.join(workflows_dir, filename)) as f:
                workflow = yaml.safe_load(f)
                if not workflow:
                    logger.error(f"Empty workflow configuration in {filename}")
                    has_invalid_workflow = True
                    continue
                if not validate_workflow(workflow):
                    logger.error(f"Invalid workflow configuration in {filename}")
                    has_invalid_workflow = True
                    continue
                config["workflows"].append(workflow)
        except Exception as e:
            logger.error(f"Error loading workflow {filename}: {e}")
            has_invalid_workflow = True
            continue
    
    if has_invalid_workflow:
        raise ValueError("Invalid workflow configuration")
    
    # 加载模型配置
    if os.path.exists(models_file):
        try:
            with open(models_file) as f:
                models = yaml.safe_load(f)
                if not models or "models" not in models:
                    raise ValueError("Invalid model configuration")
                for model in models["models"]:
                    if not validate_model(model):
                        raise ValueError(f"Invalid model configuration: {model.get('model_id', 'unknown')}")
                config["models"] = models["models"]
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error loading models config: {e}")
            raise ValueError(f"Error loading models config: {e}")
    
    # 加载工具配置
    if os.path.exists(tools_file):
        try:
            with open(tools_file) as f:
                tools = yaml.safe_load(f)
                if not tools or "tools" not in tools:
                    raise ValueError("Invalid tool configuration")
                for tool in tools["tools"]:
                    if not validate_tool(tool):
                        raise ValueError(f"Invalid tool configuration: {tool.get('name', 'unknown')}")
                config["tools"] = tools["tools"]
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error loading tools config: {e}")
            raise ValueError(f"Error loading tools config: {e}")
    
    return config

# 默认配置路径
DEFAULT_WORKFLOWS_DIR = "app/instances/workflows"
DEFAULT_MODELS_FILE = "app/instances/models.yaml"
DEFAULT_TOOLS_FILE = "app/instances/tools.yaml" 