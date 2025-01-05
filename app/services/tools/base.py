from typing import Dict, Any

class BaseTool:
    """基础工具类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "")
        self.description = config.get("description", "")
        self.parameters = config.get("parameters", {})
    
    async def __call__(self, input_text: str, **kwargs) -> str:
        """
        执行工具
        
        Args:
            input_text: 输入文本
            **kwargs: 额外参数
            
        Returns:
            str: 执行结果
        """
        raise NotImplementedError("Tool must implement __call__ method") 