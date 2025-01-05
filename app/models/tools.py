from pydantic import BaseModel
from typing import Dict, Any, Optional

class ToolConfig(BaseModel):
    name: str
    description: str
    class_name: str
    module: str
    params: Optional[Dict[str, Any]] = None 