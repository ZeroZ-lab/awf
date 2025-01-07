import yaml
import os
import logging
from typing import Dict, Any, List
from app.models.tools import ToolConfig
from app.models.agents import AgentConfig
from app.models.workflows import WorkflowConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def validate_workflow(workflow: Dict[str, Any]) -> bool:
    """验证工作流配置"""
    required_fields = ["workflow_id", "name", "steps"]
    
    # 基本字段验证
    if not all(field in workflow for field in required_fields):
        missing_fields = [field for field in required_fields if field not in workflow]
        logger.error(f"Missing required fields in workflow config: {missing_fields}")
        return False
        
    # 类型验证
    if not isinstance(workflow["workflow_id"], str):
        logger.error("workflow_id must be a string")
        return False
    if not isinstance(workflow["name"], str):
        logger.error("name must be a string")
        return False
    if not isinstance(workflow["steps"], list):
        logger.error("steps must be a list")
        return False
        
    # 步骤验证
    for i, step in enumerate(workflow["steps"]):
        if "type" not in step:
            logger.error(f"Step {i} missing type field")
            return False
        if step["type"] == "llm":
            if "model" not in step:
                logger.error(f"LLM step {i} missing model field")
                return False
            if "prompt_template" not in step:
                logger.error(f"LLM step {i} missing prompt_template field")
                return False
        elif step["type"] == "if":
            if "condition" not in step:
                logger.error(f"If step {i} missing condition field")
                return False
            if "then" not in step and "else" not in step:
                logger.error(f"If step {i} missing then/else branches")
                return False
                
    return True

def validate_model(model: Dict[str, Any]) -> bool:
    """验证模型配置"""
    required_fields = ["model_id", "name", "type", "params"]
    
    # 基本字段验证
    if not all(field in model for field in required_fields):
        missing_fields = [field for field in required_fields if field not in model]
        logger.error(f"Missing required fields in model config: {missing_fields}")
        return False
        
    # 类型验证
    if not isinstance(model["model_id"], str):
        logger.error("model_id must be a string")
        return False
    if not isinstance(model["name"], str):
        logger.error("name must be a string")
        return False
    if not isinstance(model["type"], str):
        logger.error("type must be a string")
        return False
    if not isinstance(model["params"], dict):
        logger.error("params must be a dictionary")
        return False
        
    # 模型类型特定验证
    if model["type"] == "openai":
        if "api_key_env" not in model["params"]:
            logger.error("OpenAI model requires api_key_env in params")
            return False
        if "model_name" not in model["params"]:
            logger.error("OpenAI model requires model_name in params")
            return False
    elif model["type"] == "openrouter":
        if "api_key_env" not in model["params"]:
            logger.error("OpenRouter model requires api_key_env in params")
            return False
        if "model_name" not in model["params"]:
            logger.error("OpenRouter model requires model_name in params")
            return False
            
    return True

def validate_tool(tool: Dict[str, Any]) -> bool:
    """验证工具配置"""
    required_fields = ["name", "description", "class_name", "module"]
    
    # 基本字段验证
    if not all(field in tool for field in required_fields):
        missing_fields = [field for field in required_fields if field not in tool]
        logger.error(f"Missing required fields in tool config: {missing_fields}")
        return False
        
    # 类型验证
    if not isinstance(tool["name"], str):
        logger.error("name must be a string")
        return False
    if not isinstance(tool["description"], str):
        logger.error("description must be a string")
        return False
    if not isinstance(tool["class_name"], str):
        logger.error("class_name must be a string")
        return False
    if not isinstance(tool["module"], str):
        logger.error("module must be a string")
        return False
        
    # 模块路径验证
    if not tool["module"].startswith("app."):
        logger.error("module path must start with 'app.'")
        return False
        
    return True

def validate_config(config: Dict[str, Any]) -> List[str]:
    """验证配置"""
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
    model_ids = set()
    for model in config.get("models", []):
        if not validate_model(model):
            errors.append(f"模型配置无效: {model.get('model_id', 'unknown')}")
        if model["model_id"] in model_ids:
            errors.append(f"重复的模型ID: {model['model_id']}")
        model_ids.add(model["model_id"])
    
    # 验证工作流配置
    workflow_ids = set()
    for workflow in config.get("workflows", []):
        if not validate_workflow(workflow):
            errors.append(f"工作流配置无效: {workflow.get('workflow_id', 'unknown')}")
        if workflow["workflow_id"] in workflow_ids:
            errors.append(f"重复的工作流ID: {workflow['workflow_id']}")
        workflow_ids.add(workflow["workflow_id"])
        
        # 验证工作流中引用的模型是否存在
        for step in workflow["steps"]:
            if step["type"] == "llm" and step["model"] not in model_ids:
                errors.append(f"工作流 {workflow['workflow_id']} 引用了不存在的模型: {step['model']}")
    
    return errors

def load_workflow_file(filepath: str) -> Dict[str, Any]:
    """加载单个工作流文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # 预处理 YAML 内容，处理可能的 BOM
            if content.startswith('\ufeff'):
                content = content[1:]
            workflow = yaml.safe_load(content)
            if not workflow:
                raise ValueError("Empty workflow configuration")
            if not validate_workflow(workflow):
                missing_fields = [field for field in ["workflow_id", "name", "steps"] if field not in workflow]
                raise ValueError(f"Missing required fields: {missing_fields}")
            return workflow
    except Exception as e:
        raise ValueError(f"Failed to load workflow: {str(e)}")

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
    
    # 获取工作目录的绝对路径
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 标准化路径
    workflows_dir = os.path.normpath(os.path.join(base_dir, workflows_dir))
    models_file = os.path.normpath(os.path.join(base_dir, models_file))
    tools_file = os.path.normpath(os.path.join(base_dir, tools_file))
    
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"Loading workflows from: {workflows_dir}")
    logger.info(f"Loading models from: {models_file}")
    logger.info(f"Loading tools from: {tools_file}")
    
    # 加载工作流配置
    if not os.path.exists(workflows_dir):
        logger.warning(f"Workflows directory not found: {workflows_dir}")
        return config
        
    workflow_files = [f for f in os.listdir(workflows_dir) if f.endswith(".yaml")]
    if not workflow_files:
        logger.warning(f"No workflow files found in {workflows_dir}")
        return config
        
    invalid_workflows = []
    for filename in workflow_files:
        filepath = os.path.join(workflows_dir, filename)
        try:
            workflow = load_workflow_file(filepath)
            config["workflows"].append(workflow)
        except ValueError as e:
            logger.error(f"Error loading workflow {filename}: {e}")
            invalid_workflows.append(f"{filename}: {str(e)}")
            continue
    
    if not config["workflows"]:
        error_msg = "No valid workflow configurations found. Errors:\n" + "\n".join(invalid_workflows)
        raise ValueError(error_msg)
    
    if invalid_workflows:
        logger.warning(f"Some workflows failed to load:\n{chr(10).join(invalid_workflows)}")
    
    # 加载模型配置
    if os.path.exists(models_file):
        try:
            with open(models_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.startswith('\ufeff'):
                    content = content[1:]
                models_config = yaml.safe_load(content)
                if not models_config:
                    raise ValueError("Invalid model configuration")
                
                # 处理 includes
                if "includes" in models_config:
                    models_dir = os.path.dirname(models_file)
                    for include in models_config["includes"]:
                        include_path = os.path.normpath(os.path.join(models_dir, include))
                        logger.info(f"Loading included model file: {include_path}")
                        if os.path.exists(include_path):
                            with open(include_path, 'r', encoding='utf-8') as inc_f:
                                content = inc_f.read()
                                if content.startswith('\ufeff'):
                                    content = content[1:]
                                included_config = yaml.safe_load(content)
                                if included_config and "models" in included_config:
                                    for model in included_config["models"]:
                                        if validate_model(model):
                                            config["models"].append(model)
                                        else:
                                            raise ValueError(f"Invalid model configuration in {include}: {model.get('model_id', 'unknown')}")
                        else:
                            logger.warning(f"Included model file not found: {include_path}")
                elif "models" in models_config:
                    for model in models_config["models"]:
                        if validate_model(model):
                            config["models"].append(model)
                        else:
                            raise ValueError(f"Invalid model configuration: {model.get('model_id', 'unknown')}")
                else:
                    logger.warning("No models configuration found")
                
                if not config["models"]:
                    logger.warning("No valid model configurations found")
                    
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error loading models config: {e}")
            raise ValueError(f"Error loading models config: {e}")
    
    # 加载工具配置
    if os.path.exists(tools_file):
        try:
            with open(tools_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.startswith('\ufeff'):
                    content = content[1:]
                tools_config = yaml.safe_load(content)
                if not tools_config:
                    raise ValueError("Invalid tool configuration")
                
                # 处理 includes
                if "includes" in tools_config:
                    tools_dir = os.path.dirname(tools_file)
                    for include in tools_config["includes"]:
                        include_path = os.path.normpath(os.path.join(tools_dir, include))
                        logger.info(f"Loading included tool file: {include_path}")
                        if os.path.exists(include_path):
                            with open(include_path, 'r', encoding='utf-8') as inc_f:
                                content = inc_f.read()
                                if content.startswith('\ufeff'):
                                    content = content[1:]
                                included_config = yaml.safe_load(content)
                                if included_config and "tools" in included_config:
                                    for tool in included_config["tools"]:
                                        if validate_tool(tool):
                                            config["tools"].append(tool)
                                        else:
                                            raise ValueError(f"Invalid tool configuration in {include}: {tool.get('name', 'unknown')}")
                        else:
                            logger.warning(f"Included tool file not found: {include_path}")
                elif "tools" in tools_config:
                    for tool in tools_config["tools"]:
                        if validate_tool(tool):
                            config["tools"].append(tool)
                        else:
                            raise ValueError(f"Invalid tool configuration: {tool.get('name', 'unknown')}")
                else:
                    logger.warning("No tools configuration found")
                
                if not config["tools"]:
                    logger.warning("No valid tool configurations found")
                    
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