import os
from typing import Dict, Any, Type, Optional
from app.models.agents import ModelConfig
from app.services.providers.base import BaseProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.openrouter_provider import OpenRouterProvider
from app.services.providers.deepseek_provider import DeepSeekProvider
from app.core.config_loader import ConfigLoader
from app.services.interfaces import BaseModelManager
from app.services.decorators import retry_async, monitor_performance, cache_result
from dotenv import load_dotenv
import logging
import asyncio

logger = logging.getLogger(__name__)

load_dotenv()

PROVIDER_MAP: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "openrouter": OpenRouterProvider,
    "deepseek": DeepSeekProvider
}

class ModelManager(BaseModelManager):
    def __init__(self):
        self.models: Dict[str, BaseProvider] = {}
        self.config_loader = ConfigLoader()
        self._ready = asyncio.Event()
        self._init_task = None
        
    async def initialize(self):
        """初始化模型管理器"""
        if self._init_task is None:
            self._init_task = asyncio.create_task(self.load_models())
            await self._init_task
        
    async def wait_until_ready(self):
        """等待模型管理器初始化完成"""
        if self._init_task is None:
            await self.initialize()
        await self._ready.wait()
    
    @monitor_performance("model_manager", "register_model")
    async def register_model(self, model_id: str, model: BaseProvider) -> None:
        """注册模型"""
        self.models[model_id] = model
        logger.info(f"Registered model: {model_id}")

    @monitor_performance("model_manager", "get_model")
    async def get_model(self, model_id: str) -> Optional[BaseProvider]:
        """获取指定ID的模型"""
        await self.wait_until_ready()  # 确保模型已加载
        logger.info(f"Getting model: {model_id}")
        logger.info(f"Available models: {list(self.models.keys())}")
        
        model = self.models.get(model_id)
        if not model:
            logger.error(f"Model not found 3: {model_id}")
            return None
            
        logger.info(f"Found model: {model_id}")
        return model

    @retry_async(retries=3, delay=1.0, exceptions=(ValueError,))
    async def create_model(self, config: ModelConfig) -> BaseProvider:
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
        if not await provider.validate_config():
            raise ValueError(f"Invalid configuration for provider: {config.type}")
        
        return provider

    @monitor_performance("model_manager", "load_models")
    async def load_models(self, models_file: str = "app/instances/models.yaml") -> None:
        """加载模型配置"""
        try:
            # 获取工作目录的绝对路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            # 标准化路径
            models_file = os.path.normpath(os.path.join(base_dir, models_file))
            logger.info(f"Loading models from: {models_file}")
            
            # 使用新的配置加载器
            models_data = self.config_loader.load_config(models_file)
            logger.info(f"Loaded models data: {models_data}")
            
            # 清空现有模型
            self.models.clear()
            
            if not models_data:
                logger.warning("No models data found")
                await self._load_default_models()
                return
                
            if not models_data.get("models"):
                logger.warning("No models list found in config")
                await self._load_default_models()
                return

            has_valid_models = False
            for model_data in models_data.get("models", []):
                try:
                    logger.info(f"Creating model from config: {model_data}")
                    model_config = ModelConfig(**model_data)
                    logger.info(f"Created model config: {model_config}")
                    
                    model = await self.create_model(model_config)
                    logger.info(f"Created model instance: {model}")
                    
                    await self.register_model(model_config.model_id, model)
                    has_valid_models = True
                    logger.info(f"Successfully loaded model: {model_config.model_id}")
                except Exception as e:
                    logger.error(f"Error creating model {model_data.get('model_id')}: {str(e)}", exc_info=True)

            if not has_valid_models:
                logger.warning("No valid models loaded, using defaults")
                await self._load_default_models()
            else:
                logger.info(f"Successfully loaded models: {list(self.models.keys())}")

        except Exception as e:
            logger.error(f"Error loading models config: {str(e)}", exc_info=True)
            await self._load_default_models()
        finally:
            # 标记初始化完成
            self._ready.set()
            logger.info("Model manager initialization completed")

    @retry_async(retries=3, delay=1.0)
    async def _load_default_models(self):
        """加载默认模型配置"""
        # 清空现有模型
        self.models.clear()
        
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
            ),
            ModelConfig(
                model_id="deepseek-chat",
                name="DeepSeek Chat",
                type="deepseek",
                params={
                    "model_name": "deepseek-chat",
                    "api_key_env": "DEEPSEEK_API_KEY"
                }
            )
        ]
        
        for config in default_configs:
            try:
                model = await self.create_model(config)
                await self.register_model(config.model_id, model)
                logger.info(f"Created default model: {config.model_id}")
            except Exception as e:
                logger.error(f"Error creating default model {config.model_id}: {e}")

    @monitor_performance("model_manager", "list_models")
    async def list_models(self) -> Dict[str, str]:
        """列出所有可用的模型

        Returns:
            Dict[str, str]: 模型ID到模型名称的映射
        """
        await self.wait_until_ready()  # 确保模型已加载
        return {model_id: model.config.name for model_id, model in self.models.items()}

# 创建全局模型管理器实例
models = ModelManager() 
