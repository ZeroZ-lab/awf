from typing import Generator
from app.core.config import config
from app.services.tool_manager import tools_registry
from app.services.model_manager import models

def get_config() -> dict:
    return config

def get_tools() -> dict:
    return tools_registry

def get_models() -> dict:
    return models 