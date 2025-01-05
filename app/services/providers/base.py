from abc import ABC, abstractmethod
from typing import Dict, Any
from app.models.agents import ModelConfig

class BaseProvider(ABC):
    def __init__(self, config: ModelConfig):
        self.config = config

    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置"""
        pass 