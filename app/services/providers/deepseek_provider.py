import os
from openai import OpenAI
from typing import Dict, Any
from .base import BaseProvider

class DeepSeekProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        api_key = os.getenv(config.params["api_key_env"])
        if not api_key:
            raise ValueError(f"API key not found in environment: {config.params['api_key_env']}")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = config.params["model_name"]

    def generate_text(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7),
                **{k:v for k,v in kwargs.items() if k not in ["max_tokens", "temperature"]}
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"DeepSeek API error: {e}")
            return f"Error generating text with DeepSeek: {str(e)}"

    def validate_config(self) -> bool:
        required_params = ["api_key_env", "model_name"]
        return all(param in self.config.params for param in required_params) 