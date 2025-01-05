from typing import Dict, Any, List, Optional, AsyncGenerator
from app.services.agent_executor import run_react_agent
from app.services.model_manager import models
from app.services.condition_executor import ConditionExecutorFactory
from app.core.config import config
import logging
import json
import time
import asyncio

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
        self.condition_executor_factory = ConditionExecutorFactory(self._execute_step)
        logger.info(f"Initializing workflow: {workflow_config.get('workflow_id')}")

    async def execute(self, input_text: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """执行工作流

        Args:
            input_text: 输入文本
            parameters: 可选的参数字典，用于在工作流执行过程中替换变量

        Returns:
            str: 执行结果
        """
        # 合并工作流默认参数和用户参数
        default_params = self.workflow_config.get("parameters", {})
        user_params = parameters or {}
        merged_params = {**default_params, **user_params}
        
        self.context["input"] = input_text
        self.context["parameters"] = merged_params
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
        # 合并工作流默认参数和用户参数
        default_params = self.workflow_config.get("parameters", {})
        user_params = parameters or {}
        merged_params = {**default_params, **user_params}
        
        self.context["input"] = input_text
        self.context["parameters"] = merged_params
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
        step_type = step.get("type")
        
        # 处理条件步骤
        if step_type in ["if", "switch", "match"]:
            executor = self.condition_executor_factory.get_executor(step_type)
            return await executor.execute(step, input_text, self.context)
        
        # 处理 LLM 步骤
        elif step_type == "llm":
            model_id = step.get("model")
            if not model_id:
                raise ValueError("Model ID is required for llm step")
            
            model = models.get_model(model_id)
            if not model:
                raise ValueError(f"Model not found: {model_id}")
            
            try:
                # 格式化提示词，支持参数替换
                format_args = {
                    "input_text": input_text,
                    **(self.context.get("parameters") or {})
                }
                prompt = step.get("prompt_template", "{input_text}").format(**format_args)
                
                # 获取其他 LLM 参数
                temperature = step.get("temperature", 0.7)
                max_tokens = step.get("max_tokens")
                stop_sequences = step.get("stop_sequences", [])
                
                # 调用模型生成文本
                result = await model.generate_text(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stop_sequences=stop_sequences
                )
                
                logger.info(f"Generated text length: {len(result)}")
                return result
                
            except KeyError as e:
                logger.error(f"Missing parameter in prompt template: {e}")
                raise ValueError(f"Missing parameter in prompt template: {e}")
            except Exception as e:
                logger.error(f"Error generating text: {e}")
                raise
        
        # 处理 agent 步骤
        elif step_type == "agent":
            model_id = step.get("model")
            if not model_id:
                raise ValueError("Model ID is required for agent step")
            
            model = models.get_model(model_id)
            if not model:
                raise ValueError(f"Model not found: {model_id}")
            
            tools = step.get("tools", [])
            return await run_react_agent(model, input_text, tools)
            
        else:
            raise ValueError(f"Unknown step type: {step_type}")

    def _format_result(self, result: Any) -> str:
        """格式化执行结果"""
        if isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False)
        return str(result) 