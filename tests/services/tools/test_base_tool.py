import pytest
from typing import Dict, Any
from app.services.tools.base import BaseTool

class TestTool(BaseTool):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    async def __call__(self, input_text: str, **kwargs) -> str:
        return f"Tool processed: {input_text}"

@pytest.fixture
def test_config():
    return {
        "name": "test_tool",
        "description": "A test tool",
        "parameters": {
            "param1": "value1",
            "param2": "value2"
        }
    }

@pytest.fixture
def tool(test_config):
    return TestTool(test_config)

def test_tool_initialization(tool, test_config):
    """测试工具初始化"""
    assert tool.config == test_config
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert tool.parameters == {"param1": "value1", "param2": "value2"}

@pytest.mark.asyncio
async def test_tool_call(tool):
    """测试工具调用"""
    input_text = "test input"
    result = await tool(input_text)
    assert result == "Tool processed: test input"

@pytest.mark.asyncio
async def test_tool_call_with_kwargs(tool):
    """测试带参数的工具调用"""
    input_text = "test input"
    result = await tool(input_text, extra_param="value")
    assert result == "Tool processed: test input" 