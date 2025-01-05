from app.tools.base import BaseTool
import math

class CalculateTool(BaseTool):
    def __init__(self, name: str = "calculate", description: str = "数学计算"):
        super().__init__(name, description)
        
    def __call__(self, expression: str) -> str:
        try:
            # 警告：eval 可能有安全风险，实际应用中应该使用更安全的方法
            result = eval(expression, {"__builtins__": {}}, {"math": math})
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}" 