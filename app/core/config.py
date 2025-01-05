import yaml
import os
from typing import Dict, Any, List
from app.models.tools import ToolConfig
from app.models.agents import AgentConfig
from app.models.workflows import WorkflowConfig

def validate_config(config: Dict[str, Any]) -> List[str]:
    if not config:
        return ["配置为空"]
        
    errors = []
    
    # 验证工具配置
    tool_names = set()
    for tool in config.get("tools", []):
        if tool["name"] in tool_names:
            errors.append(f"重复的工具名称: {tool['name']}")
        tool_names.add(tool["name"])
    
    # 验证 Agent 配置
    for agent in config.get("agents", []):
        for tool_name in agent.get("tools", []):
            if tool_name not in tool_names:
                errors.append(f"Agent {agent['agent_id']} 使用了未定义的工具: {tool_name}")
    
    return errors

def load_config() -> Dict[str, Any]:
    config = {
        "tools": [],
        "agents": [],
        "workflows": [],
        "models": []
    }
    
    # 确保配置目录存在
    os.makedirs("config/agents", exist_ok=True)
    os.makedirs("config/workflows", exist_ok=True)
    
    config_dir = "config"
    
    # 加载工具配置
    tools_file = os.path.join(config_dir, "tools.yaml")
    if os.path.exists(tools_file):
        try:
            with open(tools_file, "r") as f:
                tools_data = yaml.safe_load(f)
                if tools_data and "tools" in tools_data:
                    config["tools"] = tools_data["tools"]
        except Exception as e:
            print(f"Error loading tools config: {e}")

    # 加载模型配置
    models_file = os.path.join(config_dir, "models.yaml")
    if os.path.exists(models_file):
        try:
            with open(models_file, "r") as f:
                models_data = yaml.safe_load(f)
                if models_data and "models" in models_data:
                    config["models"] = models_data["models"]
        except Exception as e:
            print(f"Error loading models config: {e}")

    # 加载 agents 配置
    agents_dir = os.path.join(config_dir, "agents")
    if os.path.exists(agents_dir):
        for filename in os.listdir(agents_dir):
            if filename.endswith(".yaml"):
                try:
                    with open(os.path.join(agents_dir, filename), "r") as f:
                        agent_data = yaml.safe_load(f)
                        if agent_data:
                            config["agents"].append(agent_data)
                except Exception as e:
                    print(f"Error loading agent config {filename}: {e}")

    # 加载 workflows 配置
    workflows_dir = os.path.join(config_dir, "workflows")
    if os.path.exists(workflows_dir):
        for filename in os.listdir(workflows_dir):
            if filename.endswith(".yaml"):
                try:
                    with open(os.path.join(workflows_dir, filename), "r") as f:
                        workflow_data = yaml.safe_load(f)
                        if workflow_data:
                            config["workflows"].append(workflow_data)
                            print(f"Loaded workflow: {workflow_data.get('workflow_id')}")  # 添加日志
                except Exception as e:
                    print(f"Error loading workflow config {filename}: {e}")

    # 打印加载的配置信息
    print(f"Loaded {len(config['tools'])} tools")
    print(f"Loaded {len(config['agents'])} agents")
    print(f"Loaded {len(config['models'])} models")
    print(f"Loaded {len(config['workflows'])} workflows")
    
    return config

# 加载配置
config = load_config()

# 验证配置
if config:
    errors = validate_config(config)
    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"- {error}") 