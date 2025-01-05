import os
import requests
from typing import Dict, Any
from .base import BaseProvider

class OpenRouterProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = os.getenv(config.params["api_key_env"])
        if not self.api_key:
            raise ValueError(f"API key not found in environment: {config.params['api_key_env']}")
        self.model_name = config.params["model_name"]
        self.api_base = config.params.get("api_base", "https://openrouter.ai/api/v1")

    def generate_text(self, prompt: str, **kwargs) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8000"),
                "X-Title": os.getenv("APP_NAME", "AI Workflow Service")
            }

            response = requests.post(
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
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"OpenRouter API error: {e}")
            return f"Error generating text with OpenRouter: {str(e)}"

    def validate_config(self) -> bool:
        required_params = ["api_key_env", "model_name"]
        return all(param in self.config.params for param in required_params) 