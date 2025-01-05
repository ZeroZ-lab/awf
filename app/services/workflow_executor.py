from typing import Dict, Any, List, Optional, AsyncGenerator
from app.services.agent_executor import run_react_agent
from app.services.model_manager import models
from app.core.config import config
import logging
import json
import time

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    def __init__(self, workflow_config: Dict[str, Any]):
        self.workflow_config = workflow_config
        self.context = {
            "workflow_id": workflow_config.get("workflow_id"),
            "steps_results": [],
            "input": None,
            "parameters": None,
            "final_result": None
        }
        logger.info(f"Initializing workflow: {workflow_config.get('workflow_id')}")

    async def execute(self, input_text: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """执行工作流

        Args:
            input_text: 输入文本
            parameters: 可选的参数字典，用于在工作流执行过程中替换变量

        Returns:
            str: 执行结果
        """
        self.context["input"] = input_text
        self.context["parameters"] = parameters or {}
        current_input = input_text
        
        steps = self.workflow_config.get("steps", [])
        logger.info(f"Executing workflow with {len(steps)} steps")
        
        for i, step in enumerate(steps):
            try:
                logger.info(f"Executing step {i+1}/{len(steps)}: {step.get('type')}")
                
                # 执行步骤
                step_result = await self._execute_step(step, current_input)
                
                # 保存步骤结果
                step_output = {
                    "step_index": i,
                    "step_type": step.get("type"),
                    "input": current_input,
                    "output": step_result
                }
                self.context["steps_results"].append(step_output)
                
                # 更新当前输入为上一步的输出
                current_input = step_result
                
                logger.info(f"Step {i+1} completed. Output length: {len(str(step_result))}")
                
            except Exception as e:
                logger.error(f"Error in step {i+1}: {str(e)}")
                raise
        
        self.context["final_result"] = current_input
        return self._format_result(current_input)

    async def stream_execute(self, input_text: str, parameters: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流

        Args:
            input_text: 输入文本
            parameters: 可选的参数字典，用于在工作流执行过程中替换变量

        Yields:
            Dict[str, Any]: 包含执行状态和结果的字典
        """
        self.context["input"] = input_text
        self.context["parameters"] = parameters or {}
        current_input = input_text
        
        steps = self.workflow_config.get("steps", [])
        total_steps = len(steps)
        
        # 发送工作流开始信息
        yield {
            "type": "workflow_start",
            "workflow_id": self.workflow_config.get("workflow_id"),
            "total_steps": total_steps,
            "timestamp": time.time()
        }
        
        for i, step in enumerate(steps):
            try:
                # 发送步骤开始信息
                yield {
                    "type": "step_start",
                    "step_index": i,
                    "step_type": step.get("type"),
                    "total_steps": total_steps,
                    "timestamp": time.time()
                }
                
                # 执行步骤
                step_result = await self._execute_step(step, current_input)
                
                # 保存步骤结果
                step_output = {
                    "step_index": i,
                    "step_type": step.get("type"),
                    "input": current_input,
                    "output": step_result
                }
                self.context["steps_results"].append(step_output)
                
                # 发送步骤完成信息
                yield {
                    "type": "step_complete",
                    "step_index": i,
                    "step_type": step.get("type"),
                    "result": step_result,
                    "timestamp": time.time()
                }
                
                # 更新当前输入为上一步的输出
                current_input = step_result
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error in step {i+1}: {error_msg}")
                
                # 发送错误信息
                yield {
                    "type": "error",
                    "step_index": i,
                    "error": error_msg,
                    "timestamp": time.time()
                }
                return
        
        # 发送工作流完成信息
        self.context["final_result"] = current_input
        yield {
            "type": "workflow_complete",
            "result": self._format_result(current_input),
            "timestamp": time.time()
        }

    async def _execute_step(self, step: Dict[str, Any], input_text: str) -> str:
        """执行单个步骤"""
        step_type = step["type"]
        logger.info(f"Processing step type: {step_type}")
        
        if step_type == "llm":
            model_name = step["model"]
            logger.info(f"Using LLM model: {model_name}")
            model = models.get(model_name)
            if not model:
                raise ValueError(f"Model not found: {model_name}")
            
            # 格式化提示词，支持参数替换
            prompt = step["prompt_template"].format(
                input_text=input_text,
                context=self._get_context_for_prompt(),
                **self.context["parameters"]
            )
            return model.generate_text(prompt)
            
        elif step_type == "agent":
            agent_id = step["agent_id"]
            logger.info(f"Using Agent: {agent_id}")
            agent_config = None
            for agent in config.get("agents", []):
                if agent["agent_id"] == agent_id:
                    agent_config = agent
                    break
                    
            if not agent_config:
                raise ValueError(f"Agent not found: {agent_id}")
                
            # 格式化任务描述，支持参数替换
            task = step.get("task", "").format(
                input_text=input_text,
                **self.context["parameters"]
            )
            return await run_react_agent(task, agent_config)
            
        elif step_type == "workflow":
            workflow_id = step["workflow_id"]
            logger.info(f"Using nested workflow: {workflow_id}")
            workflow_config = None
            for workflow in config.get("workflows", []):
                if workflow["workflow_id"] == workflow_id:
                    workflow_config = workflow
                    break
                    
            if not workflow_config:
                raise ValueError(f"Workflow not found: {workflow_id}")
                
            nested_workflow = WorkflowExecutor(workflow_config)
            return await nested_workflow.execute(input_text, self.context["parameters"])
            
        else:
            raise ValueError(f"Unknown step type: {step_type}")

    def _get_context_for_prompt(self) -> str:
        """获取用于提示的上下文信息"""
        context_info = {
            "original_input": self.context["input"],
            "parameters": self.context["parameters"],
            "previous_steps": [
                {
                    "type": step["step_type"],
                    "output": step["output"]
                }
                for step in self.context["steps_results"]
            ]
        }
        return json.dumps(context_info, ensure_ascii=False, indent=2)

    def _format_result(self, result: str) -> str:
        """格式化最终结果"""
        try:
            # 如果结果是JSON字符串，尝试美化它
            result_obj = json.loads(result)
            return json.dumps(result_obj, ensure_ascii=False, indent=2)
        except:
            # 如果不是JSON，返回原始字符串
            return result 