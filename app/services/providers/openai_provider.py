import os
from typing import Dict, Any, Optional
from .base import BaseProvider
from app.models.agents import ModelConfig
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseProvider):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.api_key = os.getenv(config.params.get("api_key_env", "OPENAI_API_KEY"))
        self.model_name = config.params.get("model_name")
        self.client = AsyncOpenAI(api_key=self.api_key)
        
    async def validate_config(self) -> bool:
        """验证配置是否有效"""
        if not self.api_key:
            logger.error("OpenAI API key not found")
            return False
        if not self.model_name:
            logger.error("Model name not specified")
            return False
        return True
        
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        if not await self.validate_config():
            raise ValueError("Invalid configuration")
            
        try:
            # 对于 instruct 模型使用 completions API
            if "instruct" in self.model_name:
                response = await self.client.completions.create(
                    model=self.model_name,
                    prompt=prompt,
                    **kwargs
                )
                return response.choices[0].text.strip()
            
            # 对于 chat 模型使用 chat completions API
            else:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise ValueError(f"Failed to generate text: {str(e)}")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "openai",
            "model_name": self.model_name,
            "capabilities": ["text-generation", "chat"] if "instruct" not in self.model_name else ["text-generation"]
        } 