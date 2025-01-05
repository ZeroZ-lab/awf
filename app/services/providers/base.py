from abc import ABC, abstractmethod
from typing import Dict, Any
from app.models.agents import ModelConfig

class BaseProvider(ABC):
    def __init__(self, config: ModelConfig):
        self.config = config

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """异步生成文本

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            str: 生成的文本
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置

        Returns:
            bool: 配置是否有效
        """
        pass 