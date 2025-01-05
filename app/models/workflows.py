from pydantic import BaseModel
from typing import List, Dict, Any

class WorkflowConfig(BaseModel):
    workflow_id: str
    name: str
    steps: List[Dict[str, Any]] 