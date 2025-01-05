from typing import Dict, Any, List, Optional, Protocol, runtime_checkable
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

@runtime_checkable
class ConditionExecutor(Protocol):
    """条件执行器接口"""
    async def execute(self, step: Dict[str, Any], input_text: str, context: Dict[str, Any]) -> str:
        """执行条件步骤"""
        ...

class BaseConditionExecutor(ABC):
    """条件执行器基类"""
    def __init__(self, step_executor):
        """
        Args:
            step_executor: 用于执行子步骤的执行器
        """
        self.step_executor = step_executor

    @abstractmethod
    async def execute(self, step: Dict[str, Any], input_text: str, context: Dict[str, Any]) -> str:
        """执行条件步骤"""
        pass

    def _safe_eval(self, expr: str, context: Dict[str, Any], extra_context: Optional[Dict[str, Any]] = None) -> Any:
        """安全地执行表达式"""
        if not self._validate_condition(expr):
            raise ValueError(f"Invalid expression: {expr}")
        
        # 创建安全的执行环境
        safe_context = {
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "max": max,
            "min": min,
            "sum": sum,
            **context
        }
        if extra_context:
            safe_context.update(extra_context)
        
        try:
            return eval(expr, {"__builtins__": {}}, safe_context)
        except Exception as e:
            logger.error(f"Error evaluating expression: {expr}")
            raise ValueError(f"Invalid expression: {str(e)}")

    def _validate_condition(self, condition: str) -> bool:
        """验证条件表达式的安全性"""
        forbidden = ['import', 'exec', 'eval', '__', 'globals', 'locals', 'open']
        return not any(word in condition for word in forbidden)

class IfConditionExecutor(BaseConditionExecutor):
    """if 条件执行器"""
    async def execute(self, step: Dict[str, Any], input_text: str, context: Dict[str, Any]) -> str:
        # 格式化并计算条件表达式
        condition = step["condition"].format(
            input_text=input_text,
            **context["parameters"]
        )
        condition_result = self._safe_eval(condition, context)
        
        # 根据条件结果选择执行路径
        if condition_result:
            sub_steps = step["then"]
        else:
            sub_steps = step.get("else", [])
        
        # 执行选中的步骤序列
        current = input_text
        for sub_step in sub_steps:
            current = await self.step_executor(sub_step, current)
        return current

class SwitchConditionExecutor(BaseConditionExecutor):
    """switch 条件执行器"""
    async def execute(self, step: Dict[str, Any], input_text: str, context: Dict[str, Any]) -> str:
        # 获取 switch 表达式的值
        value_expr = step["value"].format(
            input_text=input_text,
            **context["parameters"]
        )
        switch_value = self._safe_eval(value_expr, context)
        
        # 查找匹配的 case
        cases = step["cases"]
        default = step.get("default", [])
        matched_steps = None
        
        for case in cases:
            case_value = self._safe_eval(case["value"], context)
            if switch_value == case_value:
                matched_steps = case["steps"]
                break
        
        # 如果没有匹配的 case，使用 default
        if matched_steps is None:
            matched_steps = default
        
        # 执行匹配的步骤
        current = input_text
        for sub_step in matched_steps:
            current = await self.step_executor(sub_step, current)
        return current

class MatchConditionExecutor(BaseConditionExecutor):
    """match 条件执行器"""
    async def execute(self, step: Dict[str, Any], input_text: str, context: Dict[str, Any]) -> str:
        # 获取 match 表达式的值
        value_expr = step["value"].format(
            input_text=input_text,
            **context["parameters"]
        )
        match_value = self._safe_eval(value_expr, context)
        
        # 遍历所有条件直到找到匹配的
        conditions = step["conditions"]
        default = step.get("default", [])
        matched_steps = None
        
        for condition in conditions:
            # 支持自定义比较逻辑
            cond_expr = condition["when"].format(
                value=match_value,
                **context["parameters"]
            )
            if self._safe_eval(cond_expr, context, {"value": match_value}):
                matched_steps = condition["steps"]
                break
        
        # 如果没有匹配的条件，使用 default
        if matched_steps is None:
            matched_steps = default
        
        # 执行匹配的步骤
        current = input_text
        for sub_step in matched_steps:
            current = await self.step_executor(sub_step, current)
        return current

class ConditionExecutorFactory:
    """条件执行器工厂"""
    def __init__(self, step_executor):
        self.executors = {
            "if": IfConditionExecutor(step_executor),
            "switch": SwitchConditionExecutor(step_executor),
            "match": MatchConditionExecutor(step_executor)
        }
    
    def get_executor(self, step_type: str) -> ConditionExecutor:
        """获取条件执行器"""
        executor = self.executors.get(step_type)
        if not executor:
            raise ValueError(f"Unknown condition type: {step_type}")
        return executor 