from typing import Dict, Any, Optional, List
from importlib import import_module
from app.models.tools import ToolConfig
from app.core.config import config
from app.tools.base import BaseTool

tools_registry: Dict[str, BaseTool] = {}

def load_tools() -> List[BaseTool]:
    tools = []
    for tool_data in config.get("tools", []):
        try:
            tool_config = ToolConfig(**tool_data)
            tool_class = get_tool_class(tool_config)
            if tool_class:
                tool = tool_class(
                    name=tool_config.name,
                    description=tool_config.description,
                    **(tool_config.params or {})
                )
                tools_registry[tool_config.name] = tool
                tools.append(tool)
        except Exception as e:
            print(f"Skipping invalid tool definition: {e}")
    return tools

def get_tool_class(tool_config: ToolConfig):
    try:
        module = import_module(tool_config.module)
        tool_class = getattr(module, tool_config.class_name)
        return tool_class
    except (ImportError, AttributeError) as e:
        print(f"Error importing tool: {tool_config.name}, Error: {e}")
        return None

def get_tool_by_name(tool_name: str) -> Optional[BaseTool]:
    return tools_registry.get(tool_name)

# 初始化工具注册表
available_tools = load_tools() 