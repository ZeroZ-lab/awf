import pytest
from app.services.tool_manager import ToolManager
from app.tools.base import BaseTool

class TestTool(BaseTool):
    def __init__(self, name: str, description: str, **kwargs):
        super().__init__(name=name, description=description)
        
    async def __call__(self, input_text: str, **kwargs) -> str:
        return f"Test tool processed: {input_text}"

@pytest.fixture
def test_configs(tmp_path):
    """创建测试配置文件"""
    # 创建配置目录
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    
    # 创建搜索工具配置
    search_config = tools_dir / "search.yaml"
    search_config.write_text("""
tools:
  - name: test_search
    description: Test search tool
    class_name: TestTool
    module: tests.services.test_tool_manager_integration
""")
    
    # 创建计算工具配置
    calculate_config = tools_dir / "calculate.yaml"
    calculate_config.write_text("""
tools:
  - name: test_calculate
    description: Test calculate tool
    class_name: TestTool
    module: tests.services.test_tool_manager_integration
""")
    
    # 创建主配置文件
    main_config = tmp_path / "tools.yaml"
    main_config.write_text(f"""
includes:
  - tools/search.yaml
  - tools/calculate.yaml
""")
    
    return {
        "base_dir": str(tmp_path),
        "main_config": str(main_config)
    }

def test_tool_manager_load_split_configs(test_configs):
    """测试加载拆分的配置文件"""
    manager = ToolManager()
    manager.config_loader.base_dir = test_configs["base_dir"]
    manager.load_tools(test_configs["main_config"])
    
    # 验证工具加载
    assert len(manager.tools) == 2
    assert "test_search" in manager.tools
    assert "test_calculate" in manager.tools
    
    # 验证工具实例
    search_tool = manager.tools["test_search"]
    assert search_tool.name == "test_search"
    assert search_tool.description == "Test search tool"
    
    calculate_tool = manager.tools["test_calculate"]
    assert calculate_tool.name == "test_calculate"
    assert calculate_tool.description == "Test calculate tool"

@pytest.mark.asyncio
async def test_tool_execution(test_configs):
    """测试工具执行"""
    manager = ToolManager()
    manager.config_loader.base_dir = test_configs["base_dir"]
    manager.load_tools(test_configs["main_config"])
    
    tool = manager.get_tool("test_search")
    assert tool is not None
    
    result = await tool("test input")
    assert result == "Test tool processed: test input"

def test_tool_manager_invalid_tool(test_configs, tmp_path):
    """测试无效的工具配置"""
    # 创建无效的工具配置
    invalid_config = tmp_path / "invalid_tool.yaml"
    invalid_config.write_text("""
tools:
  - name: invalid_tool
    description: Invalid tool
    class_name: NonExistentTool
    module: nonexistent.module
""")
    
    manager = ToolManager()
    manager.load_tools(str(invalid_config))
    
    # 验证无效工具未被加载
    assert len(manager.tools) == 0

def test_tool_manager_duplicate_tools(test_configs, tmp_path):
    """测试重复工具名称"""
    # 创建重复工具配置
    duplicate_config = tmp_path / "duplicate.yaml"
    duplicate_config.write_text("""
tools:
  - name: test_tool
    description: First tool
    class_name: TestTool
    module: tests.services.test_tool_manager_integration
  - name: test_tool
    description: Second tool
    class_name: TestTool
    module: tests.services.test_tool_manager_integration
""")
    
    manager = ToolManager()
    manager.load_tools(str(duplicate_config))
    
    # 验证只加载了一个工具
    assert len(manager.tools) == 1
    assert manager.tools["test_tool"].description == "Second tool"

def test_tool_manager_empty_config(tmp_path):
    """测试空配置"""
    # 创建空配置文件
    empty_config = tmp_path / "empty.yaml"
    empty_config.write_text("")
    
    manager = ToolManager()
    manager.load_tools(str(empty_config))
    
    # 验证没有工具被加载
    assert len(manager.tools) == 0 