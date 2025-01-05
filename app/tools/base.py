from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    def __init__(self, name: str, description: str, **kwargs):
        self.name = name
        self.description = description

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """工具执行方法"""
        pass 