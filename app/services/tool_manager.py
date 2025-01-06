from typing import Dict, Any, Optional, List
from importlib import import_module
from app.models.tools import ToolConfig
from app.core.config_loader import ConfigLoader
from app.tools.base import BaseTool
import logging

logger = logging.getLogger(__name__)

class ToolManager:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.config_loader = ConfigLoader()
        self.load_tools()

    def register_tool(self, name: str, tool: BaseTool) -> None:
        """注册工具

        Args:
            name: 工具名称
            tool: 工具实例
        """
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具

        Args:
            name: 工具名称

        Returns:
            Optional[BaseTool]: 工具实例，如果不存在则返回None
        """
        tool = self.tools.get(name)
        if not tool:
            logger.warning(f"Tool not found: {name}")
        return tool

    def get_tool_class(self, tool_config: ToolConfig):
        """获取工具类

        Args:
            tool_config: 工具配置

        Returns:
            Optional[Type[BaseTool]]: 工具类，如果不存在则返回None
        """
        try:
            module = import_module(tool_config.module)
            tool_class = getattr(module, tool_config.class_name)
            return tool_class
        except (ImportError, AttributeError) as e:
            logger.error(f"Error importing tool: {tool_config.name}, Error: {e}")
            return None

    def load_tools(self, tools_file: str = "app/instances/tools.yaml") -> None:
        """加载工具配置

        Args:
            tools_file: 工具配置文件路径
        """
        try:
            # 使用新的配置加载器
            tools_data = self.config_loader.load_config(tools_file)
            if not tools_data:
                logger.warning("No tools configuration found")
                return

            for tool_data in tools_data.get("tools", []):
                try:
                    tool_config = ToolConfig(**tool_data)
                    tool_class = self.get_tool_class(tool_config)
                    if tool_class:
                        tool = tool_class(
                            name=tool_config.name,
                            description=tool_config.description,
                            **(tool_config.params or {})
                        )
                        self.register_tool(tool_config.name, tool)
                except Exception as e:
                    logger.error(f"Error creating tool {tool_data.get('name')}: {e}")

        except Exception as e:
            logger.error(f"Error loading tools config: {e}")

# 创建全局工具管理器实例
tools = ToolManager()
tools_registry = tools.tools 