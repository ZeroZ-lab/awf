from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ModelConfig(BaseModel):
    model_id: str
    name: str
    type: str
    params: Dict[str, Any]

class AgentConfig(BaseModel):
    agent_id: str
    name: str
    tools: List[str]
    llm_model: str
    prompt_template: str

class AgentResponse(BaseModel):
    result: str
    execution_time: float
    status: str 