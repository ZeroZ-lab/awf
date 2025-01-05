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
        self.input_text = None

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
        
        # Add input_text to context if available
        if hasattr(self, 'input_text'):
            safe_context['input_text'] = self.input_text
            
        if extra_context:
            safe_context.update(extra_context)
        
        try:
            return eval(expr, {"__builtins__": {}}, safe_context)
        except Exception as e:
            logger.error(f"Error evaluating expression: {expr}")
            raise ValueError(f"Invalid expression: {str(e)}")

    def _validate_condition(self, expr: str) -> bool:
        """验证条件表达式是否安全"""
        # 简单的安全检查，可以根据需要扩展
        unsafe_patterns = [
            "import",
            "exec",
            "eval(",
            "compile",
            "__",
            "globals",
            "locals",
            "open"
        ]
        return not any(pattern in expr for pattern in unsafe_patterns)

    async def _execute_steps(self, steps: List[Dict[str, Any]], input_text: str, context: Dict[str, Any]) -> Any:
        """执行步骤序列"""
        if not steps:
            return input_text
            
        current = input_text
        for step in steps:
            if self.step_executor:
                current = await self.step_executor(step, current)
        return current

class IfConditionExecutor(BaseConditionExecutor):
    """if 条件执行器"""
    async def execute(self, step: Dict[str, Any], input_text: str, context: Dict[str, Any]) -> Any:
        """执行条件步骤"""
        self.input_text = input_text  # Store input_text for evaluation
        condition = step.get("condition")
        if not condition:
            raise ValueError("Condition is required for if step")

        condition_result = self._safe_eval(condition, context)
        
        if condition_result:
            return await self._execute_steps(step.get("then", []), input_text, context)
        else:
            return await self._execute_steps(step.get("else", []), input_text, context)

class SwitchConditionExecutor(BaseConditionExecutor):
    """switch 条件执行器"""
    async def execute(self, step: Dict[str, Any], input_text: str, context: Dict[str, Any]) -> Any:
        """执行 switch 条件步骤"""
        self.input_text = input_text  # Store input_text for evaluation
        value_expr = step.get("value")
        if not value_expr:
            raise ValueError("Value expression is required for switch step")

        switch_value = self._safe_eval(value_expr, context)
        cases = step.get("cases", [])
        
        for case in cases:
            case_value = self._safe_eval(case["value"], context)
            if str(switch_value) == str(case_value):
                return await self._execute_steps(case.get("steps", []), input_text, context)
        
        # 如果没有匹配的 case，执行 default
        return await self._execute_steps(step.get("default", []), input_text, context)

class MatchConditionExecutor(BaseConditionExecutor):
    """match 条件执行器"""
    async def execute(self, step: Dict[str, Any], input_text: str, context: Dict[str, Any]) -> Any:
        """执行 match 条件步骤"""
        self.input_text = input_text  # Store input_text for evaluation
        value_expr = step.get("value")
        if not value_expr:
            raise ValueError("Value expression is required for match step")

        match_value = self._safe_eval(value_expr, context)
        conditions = step.get("conditions", [])
        
        # 添加 value 到上下文中用于条件判断
        extra_context = {"value": match_value}
        
        for condition in conditions:
            when_expr = condition.get("when")
            if not when_expr:
                continue
                
            if self._safe_eval(when_expr, context, extra_context):
                return await self._execute_steps(condition.get("steps", []), input_text, context)
        
        # 如果没有匹配的条件，执行 default
        return await self._execute_steps(step.get("default", []), input_text, context)

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