from app.tools.base import BaseTool
from typing import Any

class WorkflowTool(BaseTool):
    def __init__(self, **kwargs):
        super().__init__(name="WorkflowTool", description="用于执行工作流的工具")

    def __call__(self, workflow_id: str, **kwargs: Any) -> str:
        from app.workflow_executor import run_workflow  # 避免循环导入
        print(f"执行工作流: {workflow_id}")
        result = run_workflow(workflow_id, kwargs)
        return f"工作流 {workflow_id} 执行结果：{result}" 