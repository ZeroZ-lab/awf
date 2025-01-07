import pytest
from app.services.condition_executor import (
    ConditionExecutorFactory,
    IfConditionExecutor,
    SwitchConditionExecutor,
    MatchConditionExecutor
)

@pytest.fixture
def mock_step_executor():
    async def executor(step, input_text):
        return f"Executed: {step['type']} with {input_text}"
    return executor

@pytest.fixture
def condition_factory(mock_step_executor):
    return ConditionExecutorFactory(mock_step_executor)

@pytest.mark.asyncio
async def test_if_condition_executor(condition_factory):
    # 测试 if 条件执行器
    step = {
        "type": "if",
        "condition": "input_text.startswith('hello')",
        "then": [
            {"type": "step1", "config": "test"}
        ],
        "else": [
            {"type": "step2", "config": "test"}
        ]
    }
    
    context = {
        "input_text": "hello world",
        "parameters": {}
    }
    
    # 测试条件为真的情况
    executor = condition_factory.get_executor("if")
    executor.input_text = "hello world"  # 设置输入文本
    result = await executor.execute(step, "hello world", context)
    assert result == "Executed: step1 with hello world"
    
    # 测试条件为假的情况
    executor.input_text = "hi"  # 更新输入文本
    result = await executor.execute(step, "hi", context)
    assert result == "Executed: step2 with hi"

@pytest.mark.asyncio
async def test_switch_condition_executor(condition_factory):
    # 测试 switch 条件执行器
    step = {
        "type": "switch",
        "value": "input_text",
        "cases": [
            {
                "value": "'hello'",
                "steps": [{"type": "step1", "config": "test"}]
            },
            {
                "value": "'hello world'",
                "steps": [{"type": "step2", "config": "test"}]
            }
        ],
        "default": [{"type": "step3", "config": "test"}]
    }
    
    context = {"parameters": {}}
    
    # 测试匹配第一个 case
    executor = condition_factory.get_executor("switch")
    executor.input_text = "hello"  # 设置输入文本
    result = await executor.execute(step, "hello", context)
    assert result == "Executed: step1 with hello"
    
    # 测试匹配第二个 case
    executor.input_text = "hello world"  # 更新输入文本
    result = await executor.execute(step, "hello world", context)
    assert result == "Executed: step2 with hello world"
    
    # 测试默认情况
    executor.input_text = "hi"  # 更新输入文本
    result = await executor.execute(step, "hi", context)
    assert result == "Executed: step3 with hi"

@pytest.mark.asyncio
async def test_match_condition_executor(condition_factory):
    # 测试 match 条件执行器
    step = {
        "type": "match",
        "value": "input_text",
        "conditions": [
            {
                "when": "value.startswith('hello')",
                "steps": [{"type": "step1", "config": "test"}]
            },
            {
                "when": "value.endswith('world')",
                "steps": [{"type": "step2", "config": "test"}]
            }
        ],
        "default": [{"type": "step3", "config": "test"}]
    }
    
    context = {"parameters": {}}
    
    # 测试匹配第一个条件
    executor = condition_factory.get_executor("match")
    executor.input_text = "hello there"  # 设置输入文本
    result = await executor.execute(step, "hello there", context)
    assert result == "Executed: step1 with hello there"
    
    # 测试匹配第二个条件
    executor.input_text = "beautiful world"  # 更新输入文本
    result = await executor.execute(step, "beautiful world", context)
    assert result == "Executed: step2 with beautiful world"
    
    # 测试默认情况
    executor.input_text = "hi there"  # 更新输入文本
    result = await executor.execute(step, "hi there", context)
    assert result == "Executed: step3 with hi there"

@pytest.mark.asyncio
async def test_condition_executor_with_parameters(condition_factory):
    """测试带参数的条件执行"""
    step = {
        "type": "if",
        "condition": "input_text == vars['parameters']['expected_text']",
        "then": [
            {"type": "step1", "config": "test"}
        ],
        "else": [
            {"type": "step2", "config": "test"}
        ]
    }
    
    context = {
        "input_text": "hello",
        "parameters": {"expected_text": "hello"}
    }
    
    # 测试条件为真的情况
    executor = condition_factory.get_executor("if")
    executor.input_text = "hello"  # 设置输入文本
    result = await executor.execute(step, "hello", context)
    assert result == "Executed: step1 with hello"
    
    # 测试条件为假的情况
    context["parameters"]["expected_text"] = "world"
    result = await executor.execute(step, "hello", context)
    assert result == "Executed: step2 with hello"

@pytest.mark.asyncio
async def test_invalid_condition_expression(condition_factory):
    # 测试无效的条件表达式
    step = {
        "type": "if",
        "condition": "import os",  # 这是一个不安全的表达式
        "then": [
            {"type": "step1", "config": "test"}
        ]
    }
    
    context = {"parameters": {}}
    
    # 应该抛出 ValueError
    with pytest.raises(ValueError):
        executor = condition_factory.get_executor("if")
        await executor.execute(step, "test", context)

@pytest.mark.asyncio
async def test_unknown_condition_type():
    # 测试未知的条件类型
    factory = ConditionExecutorFactory(lambda x, y: y)
    
    with pytest.raises(ValueError):
        factory.get_executor("unknown_type") 