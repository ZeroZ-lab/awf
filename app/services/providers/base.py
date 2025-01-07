from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.agents import ModelConfig

class BaseProvider(ABC):
    """基础模型提供者"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """验证配置"""
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass 