import os
import httpx
import logging
from typing import Dict, Any
from .base import BaseProvider

logger = logging.getLogger(__name__)

class OpenRouterProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = os.getenv(config.params["api_key_env"])
        if not self.api_key:
            raise ValueError(f"API key not found in environment: {config.params['api_key_env']}")
        self.model_name = config.params["model_name"]
        self.api_base = config.params.get("api_base", "https://openrouter.ai/api/v1")

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """异步生成文本

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            str: 生成的文本

        Raises:
            Exception: 如果API调用失败
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8000"),
                "X-Title": os.getenv("APP_NAME", "AI Workflow Service"),
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": kwargs.get("max_tokens", 1000),
                        "temperature": kwargs.get("temperature", 0.7),
                        **{k:v for k,v in kwargs.items() if k not in ["max_tokens", "temperature"]}
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
                
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
                    
        except Exception as e:
            error_msg = f"Error generating text with OpenRouter: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def validate_config(self) -> bool:
        """验证配置

        Returns:
            bool: 配置是否有效
        """
        required_params = ["api_key_env", "model_name"]
        return all(param in self.config.params for param in required_params) 