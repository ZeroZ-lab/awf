from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from app.models.tools import ToolConfig
from app.models.agents import ModelConfig

class BaseModelManager(ABC):
    """模型管理器接口"""
    @abstractmethod
    async def get_model(self, model_id: str) -> Any:
        """获取模型实例"""
        pass
        
    @abstractmethod
    async def register_model(self, model_id: str, model: Any) -> None:
        """注册模型"""
        pass
        
    @abstractmethod
    async def load_models(self) -> None:
        """加载所有模型"""
        pass

class BaseToolManager(ABC):
    """工具管理器接口"""
    @abstractmethod
    async def get_tool(self, tool_name: str) -> Any:
        """获取工具实例"""
        pass
        
    @abstractmethod
    async def register_tool(self, tool_name: str, tool: Any) -> None:
        """注册工具"""
        pass
        
    @abstractmethod
    async def load_tools(self) -> None:
        """加载所有工具"""
        pass

class BaseWorkflowExecutor(ABC):
    """工作流执行器接口"""
    @abstractmethod
    async def execute(self, input_text: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """执行工作流"""
        pass
        
    @abstractmethod
    async def stream_execute(self, input_text: str, parameters: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流"""
        pass

class BaseConditionExecutor(ABC):
    """条件执行器接口"""
    @abstractmethod
    async def execute(self, step: Dict[str, Any], input_text: str, context: Dict[str, Any]) -> str:
        """执行条件步骤"""
        pass
        
    @abstractmethod
    def validate_condition(self, condition: str) -> bool:
        """验证条件表达式"""
        pass

class BaseParallelExecutor(ABC):
    """并行执行器接口"""
    @abstractmethod
    async def execute_parallel(self, steps: List[Dict[str, Any]], input_text: str, context: Dict[str, Any]) -> List[str]:
        """并行执行多个步骤"""
        pass 