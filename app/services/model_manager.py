import os
from typing import Dict, Any, Type
from app.models.agents import ModelConfig
from app.services.providers.base import BaseProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.openrouter_provider import OpenRouterProvider
from dotenv import load_dotenv
import yaml

load_dotenv()

PROVIDER_MAP: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "openrouter": OpenRouterProvider
}

def create_model(config: ModelConfig) -> BaseProvider:
    provider_class = PROVIDER_MAP.get(config.type)
    if not provider_class:
        raise ValueError(f"Unknown provider type: {config.type}")
    
    provider = provider_class(config)
    if not provider.validate_config():
        raise ValueError(f"Invalid configuration for provider: {config.type}")
    
    return provider

def load_models(models_file: str = None) -> Dict[str, BaseProvider]:
    models = {}
    
    if not models_file or not os.path.exists(models_file):
        # 默认配置
        default_configs = [
            ModelConfig(
                model_id="openai-gpt-3.5-turbo-instruct",
                name="OpenAI GPT-3.5 Turbo Instruct",
                type="openai",
                params={
                    "model_name": "gpt-3.5-turbo-instruct",
                    "api_key_env": "OPENAI_API_KEY"
                }
            ),
            ModelConfig(
                model_id="openrouter-claude-2",
                name="Claude 2 via OpenRouter",
                type="openrouter",
                params={
                    "model_name": "anthropic/claude-2",
                    "api_key_env": "OPENROUTER_API_KEY"
                }
            )
        ]
        
        for config in default_configs:
            try:
                models[config.model_id] = create_model(config)
            except Exception as e:
                print(f"Error creating model {config.model_id}: {e}")
        
        return models

    try:
        with open(models_file, "r") as f:
            models_data = yaml.safe_load(f)
            if models_data and models_data.get('models'):
                for model_data in models_data['models']:
                    try:
                        model_config = ModelConfig(**model_data)
                        model = create_model(model_config)
                        models[model_config.model_id] = model
                    except Exception as e:
                        print(f"Error creating model {model_data.get('model_id')}: {e}")
    except Exception as e:
        print(f"Error loading models config: {e}")
        # 使用默认配置
        default_config = ModelConfig(
            model_id="openai-gpt-3.5-turbo-instruct",
            name="OpenAI GPT-3.5 Turbo Instruct",
            type="openai",
            params={
                "model_name": "gpt-3.5-turbo-instruct",
                "api_key_env": "OPENAI_API_KEY"
            }
        )
        try:
            models[default_config.model_id] = create_model(default_config)
        except Exception as e:
            print(f"Error creating default model: {e}")

    return models

# 初始化模型
models = load_models("app/instances/models.yaml") 