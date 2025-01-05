import os
from typing import Dict, Any, Type, Optional
from app.models.agents import ModelConfig
from app.services.providers.base import BaseProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.openrouter_provider import OpenRouterProvider
from dotenv import load_dotenv
import yaml
import logging

logger = logging.getLogger(__name__)

load_dotenv()

PROVIDER_MAP: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "openrouter": OpenRouterProvider
}

class ModelManager:
    def __init__(self):
        self.models: Dict[str, BaseProvider] = {}
        self.load_models()
    
    def get_model(self, model_id: str) -> Optional[BaseProvider]:
        """获取指定ID的模型

        Args:
            model_id: 模型ID

        Returns:
            Optional[BaseProvider]: 模型实例，如果不存在则返回None
        """
        model = self.models.get(model_id)
        if not model:
            logger.warning(f"Model not found: {model_id}")
        return model

    def create_model(self, config: ModelConfig) -> BaseProvider:
        """创建模型实例

        Args:
            config: 模型配置

        Returns:
            BaseProvider: 模型实例

        Raises:
            ValueError: 如果提供者类型未知或配置无效
        """
        provider_class = PROVIDER_MAP.get(config.type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {config.type}")
        
        provider = provider_class(config)
        if not provider.validate_config():
            raise ValueError(f"Invalid configuration for provider: {config.type}")
        
        return provider

    def load_models(self, models_file: str = "app/instances/models.yaml") -> None:
        """加载模型配置

        Args:
            models_file: 模型配置文件路径
        """
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
                    model_id="openrouter-deepseek",
                    name="DeepSeek via OpenRouter",
                    type="openrouter",
                    params={
                        "model_name": "deepseek/deepseek-chat",
                        "api_key_env": "OPENROUTER_API_KEY"
                    }
                )
            ]
            
            for config in default_configs:
                try:
                    self.models[config.model_id] = self.create_model(config)
                    logger.info(f"Created default model: {config.model_id}")
                except Exception as e:
                    logger.error(f"Error creating model {config.model_id}: {e}")
            
            return

        try:
            with open(models_file, "r") as f:
                models_data = yaml.safe_load(f)
                if models_data and models_data.get('models'):
                    for model_data in models_data['models']:
                        try:
                            model_config = ModelConfig(**model_data)
                            model = self.create_model(model_config)
                            self.models[model_config.model_id] = model
                            logger.info(f"Loaded model from config: {model_config.model_id}")
                        except Exception as e:
                            logger.error(f"Error creating model {model_data.get('model_id')}: {e}")
        except Exception as e:
            logger.error(f"Error loading models config: {e}")
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
                self.models[default_config.model_id] = self.create_model(default_config)
                logger.info(f"Created fallback default model: {default_config.model_id}")
            except Exception as e:
                logger.error(f"Error creating default model: {e}")

    def list_models(self) -> Dict[str, str]:
        """列出所有可用的模型

        Returns:
            Dict[str, str]: 模型ID到模型名称的映射
        """
        return {model_id: model.config.name for model_id, model in self.models.items()}

# 创建全局模型管理器实例
models = ModelManager() 