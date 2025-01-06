from typing import Dict, Any
from app.services.tool_manager import tools
from app.services.model_manager import models
from app.tools.base import BaseTool

def get_tools() -> Dict[str, BaseTool]:
    return tools.tools

def get_models() -> Dict[str, Any]:
    return models.models 