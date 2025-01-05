from typing import Dict, Any, List, Optional, AsyncGenerator
from app.services.agent_executor import run_react_agent
from app.services.model_manager import models
from app.services.condition_executor import ConditionExecutorFactory
from app.core.config import load_config, DEFAULT_WORKFLOWS_DIR, DEFAULT_MODELS_FILE, DEFAULT_TOOLS_FILE
import logging
import json
import time
import asyncio

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    def __init__(self, workflow_config: Dict[str, Any]):
        """
        初始化工作流执行器
        
        Args:
            workflow_config: 工作流配置
        """
        self.workflow_config = workflow_config
        self.context = {
            "workflow_id": workflow_config.get("workflow_id"),
            "steps_results": [],
            "input": None,
            "parameters": None,
            "final_result": None
        }
        
        # 创建条件执行器
        self.condition_executor = ConditionExecutorFactory(self._execute_step)
        
        # 验证工作流配置
        if not self._validate_workflow_config(workflow_config):
            raise ValueError("Invalid workflow configuration")
    
    def _validate_workflow_config(self, config: Dict[str, Any]) -> bool:
        """验证工作流配置"""
        required_fields = ["workflow_id", "name", "steps"]
        return all(field in config for field in required_fields)
    
    async def execute(self, input_text: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        执行工作流
        
        Args:
            input_text: 输入文本
            parameters: 可选参数
            
        Returns:
            str: 执行结果
        """
        try:
            self.context["input"] = input_text
            self.context["parameters"] = parameters or {}
            self.context["steps_results"] = []  # 重置步骤结果
            
            result = None
            for step in self.workflow_config["steps"]:
                result = await self._execute_step(step, input_text)
                # 记录步骤结果
                self.context["steps_results"].append({
                    "step_type": step.get("type"),
                    "input": input_text,
                    "output": result,
                    "parameters": {
                        **self.context.get("parameters", {}),
                        **step.get("parameters", {})
                    }
                })
                input_text = result  # 使用上一步的结果作为下一步的输入
                
            self.context["final_result"] = result
            return result
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            raise
    
    async def stream_execute(self, input_text: str, parameters: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式执行工作流
        
        Args:
            input_text: 输入文本
            parameters: 可选参数
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        try:
            self.context["input"] = input_text
            self.context["parameters"] = parameters or {}
            
            total_steps = len(self.workflow_config["steps"])
            current_step = 0
            
            for step in self.workflow_config["steps"]:
                current_step += 1
                step_start_time = time.time()
                
                # 发送步骤开始事件
                yield {
                    "type": "step_start",
                    "step": current_step,
                    "total_steps": total_steps,
                    "description": step.get("description", ""),
                    "timestamp": time.time()
                }
                
                try:
                    result = await self._execute_step(step, input_text)
                    input_text = result  # 使用上一步的结果作为下一步的输入
                    
                    # 发送步骤完成事件
                    yield {
                        "type": "step_complete",
                        "step": current_step,
                        "total_steps": total_steps,
                        "result": result,
                        "execution_time": time.time() - step_start_time,
                        "timestamp": time.time()
                    }
                    
                except Exception as e:
                    # 发送步骤错误事件
                    yield {
                        "type": "step_error",
                        "step": current_step,
                        "total_steps": total_steps,
                        "error": str(e),
                        "timestamp": time.time()
                    }
                    raise
            
            # 发送完成事件
            yield {
                "type": "complete",
                "result": input_text,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            raise
    
    async def _execute_step(self, step: Dict[str, Any], input_text: str) -> str:
        """
        执行单个步骤
        
        Args:
            step: 步骤配置
            input_text: 输入文本
            
        Returns:
            str: 执行结果
        """
        step_type = step.get("type")
        
        # 处理条件步骤
        if step_type in ["if", "switch", "match"]:
            return await self.condition_executor.execute(step, input_text, self.context)
        
        # 处理 LLM 步骤
        elif step_type == "llm":
            model_id = step.get("model")
            if not model_id:
                raise ValueError("Model ID is required")
            
            model = models.get_model(model_id)
            if not model:
                raise ValueError(f"Model not found: {model_id}")
            
            # 合并参数
            params = {
                **self.context.get("parameters", {}),
                **step.get("parameters", {})
            }
            
            # 格式化提示模板
            prompt_template = step.get("prompt_template", "{input_text}")
            prompt = prompt_template.format(
                input_text=input_text,
                **self.context
            )
            
            # 生成文本
            result = await model.generate_text(prompt, **params)
            return result
        
        # 处理工具步骤
        elif step_type == "tool":
            tool_name = step.get("tool")
            if not tool_name:
                raise ValueError("Tool name is required")
            
            # TODO: 实现工具调用
            raise NotImplementedError("Tool execution not implemented yet")
        
        else:
            raise ValueError(f"Unknown step type: {step_type}")
    
    def _format_result(self, result: Any) -> str:
        """格式化结果"""
        if isinstance(result, str):
            return result
        elif isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False)
        else:
            return str(result) 