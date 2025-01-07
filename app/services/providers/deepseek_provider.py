import os
from openai import OpenAI
from typing import Dict, Any
from .base import BaseProvider
from app.models.agents import ModelConfig
import httpx
import logging

logger = logging.getLogger(__name__)

class DeepSeekProvider(BaseProvider):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.api_key = os.getenv(config.params.get("api_key_env", "DEEPSEEK_API_KEY"))
        self.model_name = config.params.get("model_name")
        self.base_url = "https://api.deepseek.com"
        
    async def validate_config(self) -> bool:
        """验证配置是否有效"""
        if not self.api_key:
            logger.error("DeepSeek API key not found")
            return False
        if not self.model_name:
            logger.error("Model name not specified")
            return False
        return True
        
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        if not await self.validate_config():
            raise ValueError("Invalid configuration")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            **{k:v for k,v in kwargs.items() if k not in ["temperature", "max_tokens"]}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                if "choices" not in result or not result["choices"]:
                    raise ValueError("No completion choices returned")
                    
                return result["choices"][0]["message"]["content"]
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            raise ValueError(f"Failed to generate text: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise ValueError(f"Failed to generate text: {str(e)}")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "deepseek",
            "model_name": self.model_name,
            "capabilities": ["text-generation", "chat"]
        } 