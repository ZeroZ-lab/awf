from typing import Dict, Any, List, Optional, AsyncGenerator
from app.services.agent_executor import run_react_agent
from app.services.model_manager import models
from app.services.condition_executor import ConditionExecutorFactory
from app.services.parallel_executor import ParallelExecutor
from app.core.config import load_config, DEFAULT_WORKFLOWS_DIR, DEFAULT_MODELS_FILE, DEFAULT_TOOLS_FILE
import logging
import json
import time
import asyncio
import re

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
            "parameters": workflow_config.get("parameters", {}),
            "steps_results": []
        }
        self.condition_executor = ConditionExecutorFactory(self._execute_step)
        self.parallel_executor = ParallelExecutor(self._execute_step)
        
        # 验证工作流配置
        if not self._validate_workflow_config(workflow_config):
            raise ValueError("Invalid workflow configuration")
    
    def _validate_workflow_config(self, config: Dict[str, Any]) -> bool:
        """验证工作流配置"""
        required_fields = ["workflow_id", "name", "steps"]
        return all(field in config for field in required_fields)
    
    async def execute(self, input_text: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """执行工作流"""
        if parameters is None:
            parameters = {}
            
        # 处理参数默认值
        workflow_params = self.workflow_config.get("parameters", {})
        processed_params = {}
        
        # 先设置所有默认值
        for param_name, param_config in workflow_params.items():
            if isinstance(param_config, dict):
                processed_params[param_name] = param_config.get("default")
        
        # 然后用用户提供的参数覆盖默认值
        for param_name, param_value in parameters.items():
            if param_name in workflow_params:
                processed_params[param_name] = param_value
        
        # 检查必需参数
        for param_name, param_config in workflow_params.items():
            if isinstance(param_config, dict) and param_config.get("required", False):
                if processed_params.get(param_name) is None:
                    logger.error(f"Missing required parameter: {param_name}")
                    logger.error(f"Parameter config: {param_config}")
                    raise ValueError(f"Missing required parameter: {param_name}")
        
        # 记录参数处理结果
        logger.info(f"Original parameters: {parameters}")
        logger.info(f"Processed parameters: {processed_params}")
            
        # 初始化上下文
        self.context = {
            "parameters": processed_params,
            "steps_results": []
        }
        
        # 执行工作流步骤
        for step in self.workflow_config.get("steps", []):
            input_text = await self._execute_step(step, input_text)
            
        return input_text
    
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
            if parameters is None:
                parameters = {}
                
            # 处理参数默认值
            workflow_params = self.workflow_config.get("parameters", {})
            processed_params = {}
            
            # 先设置所有默认值
            for param_name, param_config in workflow_params.items():
                if isinstance(param_config, dict):
                    processed_params[param_name] = param_config.get("default")
            
            # 然后用用户提供的参数覆盖默认值
            for param_name, param_value in parameters.items():
                if param_name in workflow_params:
                    processed_params[param_name] = param_value
            
            # 检查必需参数
            for param_name, param_config in workflow_params.items():
                if isinstance(param_config, dict) and param_config.get("required", False):
                    if processed_params.get(param_name) is None:
                        logger.error(f"Missing required parameter: {param_name}")
                        logger.error(f"Parameter config: {param_config}")
                        raise ValueError(f"Missing required parameter: {param_name}")
            
            # 记录参数处理结果
            logger.info(f"Original parameters: {parameters}")
            logger.info(f"Processed parameters: {processed_params}")
            
            self.context = {
                "input": input_text,
                "parameters": processed_params,
                "steps_results": []
            }
            
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
    
    def _process_template(self, template: str, context: Dict[str, Any]) -> str:
        """处理模板字符串"""
        try:
            # 替换参数引用
            pattern = r'\$param\((.*?)\)'
            matches = re.finditer(pattern, template)
            for match in matches:
                param_name = match.group(1)
                param_value = self.context["parameters"].get(param_name)
                if param_value is None:
                    logger.warning(f"Parameter not found: {param_name}, using empty string")
                    param_value = ""
                template = template.replace(match.group(0), str(param_value))
            
            # 替换函数调用，从内到外处理
            while True:
                # 查找最内层的函数调用
                pattern = r'\$(\w+)\(([^$\(\)]*)\)'
                match = re.search(pattern, template)
                if not match:
                    break
                    
                func_name = match.group(1)
                args = [arg.strip() for arg in match.group(2).split(',')]
                
                if func_name == "if":
                    if len(args) != 3:
                        raise ValueError("if function requires 3 arguments: condition, true_value, false_value")
                    condition, true_value, false_value = args
                    
                    # 处理特殊条件
                    if condition == "has_summary":
                        has_summary = any(result.get("id") == "summary" for result in self.context["steps_results"])
                        result = true_value if has_summary else false_value
                    else:
                        # 处理其他条件
                        condition_result = self._process_condition(condition, context)
                        result = true_value if condition_result else false_value
                        
                    template = template.replace(match.group(0), result)
                    
                elif func_name == "output":
                    if len(args) != 1:
                        raise ValueError("output function requires 1 argument")
                    step_id = args[0]
                    output = None
                    for result in self.context["steps_results"]:
                        if result.get("id") == step_id:
                            output = result.get("output")
                            break
                    if output is None:
                        raise ValueError(f"Step output not found: {step_id}")
                    template = template.replace(match.group(0), str(output))
                    
                elif func_name == "length":
                    if len(args) != 1:
                        raise ValueError("length function requires 1 argument")
                    step_id = args[0]
                    output = None
                    for result in self.context["steps_results"]:
                        if result.get("id") == step_id:
                            output = result.get("output")
                            break
                    if output is None:
                        raise ValueError(f"Step output not found: {step_id}")
                    value = len(output)
                    template = template.replace(match.group(0), str(value))
                    
                else:
                    raise ValueError(f"Unknown function: {func_name}")
            
            # 替换基本变量
            return template.format(**context)
            
        except KeyError as e:
            raise ValueError(f"Template variable not found: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing template: {str(e)}")
            
    def _process_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """处理条件表达式"""
        try:
            # 替换所有变量引用
            processed_condition = self._process_template(condition, context)
            
            # 将处理后的条件转换为Python表达式
            try:
                # 安全地评估条件
                result = eval(processed_condition, {"__builtins__": {}}, {})
                return bool(result)
            except Exception as e:
                raise ValueError(f"Invalid condition expression: {str(e)}")
                
        except Exception as e:
            raise ValueError(f"Error processing condition: {str(e)}")

    async def _execute_step(self, step: Dict[str, Any], input_text: str) -> str:
        """执行单个步骤"""
        step_type = step.get("type")
        step_id = step.get("id", "unknown")
        logger.info(f"Executing step {step_id} of type {step_type}")
        
        # 处理条件步骤
        if step_type == "if":
            condition = step.get("condition")
            if not condition:
                raise ValueError("Condition is required for if step")
                
            # 创建条件上下文
            context = {
                "input_text": input_text,
                "parameters": self.context.get("parameters", {}),
                "outputs": {
                    result["id"]: result["output"]
                    for result in self.context["steps_results"]
                    if "id" in result
                }
            }
            
            # 评估条件
            try:
                condition_result = self._process_condition(condition, context)
                logger.info(f"Condition '{condition}' evaluated to {condition_result}")
                logger.info(f"Available outputs: {list(context['outputs'].keys())}")
            except Exception as e:
                raise ValueError(f"Error evaluating condition: {str(e)}")
            
            # 执行相应分支
            if condition_result:
                logger.info("Executing 'then' branch")
                for then_step in step.get("then", []):
                    input_text = await self._execute_step(then_step, input_text)
            else:
                logger.info("Executing 'else' branch")
                for else_step in step.get("else", []):
                    input_text = await self._execute_step(else_step, input_text)
            return input_text
            
        # 处理 LLM 步骤
        elif step_type == "llm":
            model_id = step.get("model")
            logger.info(f"Getting model fff: {model_id}")
            if not model_id:
                raise ValueError("Model ID is required")
            
            model = await models.get_model(model_id)
            if not model:
                raise ValueError(f"Model not found 4: {model_id}")
            
            # 创建模板上下文
            context = {
                "input_text": input_text,
                "parameters": self.context.get("parameters", {}),
                "outputs": {
                    result["id"]: result["output"]
                    for result in self.context["steps_results"]
                    if "id" in result
                }
            }
            
            # 记录可用的输出
            logger.info(f"Step {step_id} - Available outputs: {list(context['outputs'].keys())}")
            
            # 处理提示模板
            prompt_template = step.get("prompt_template", "{input_text}")
            try:
                prompt = self._process_template(prompt_template, context)
                logger.info(f"Step {step_id} - Prompt template: {prompt_template}")
                logger.info(f"Step {step_id} - Processed prompt: {prompt}")
            except Exception as e:
                raise ValueError(f"Error processing template: {str(e)}")
            
            # 生成文本
            result = await model.generate_text(prompt, **step.get("parameters", {}))
            logger.info(f"Step {step_id} - Result: {result}")
            
            # 保存结果
            if "id" in step:
                self.context["steps_results"].append({
                    "id": step["id"],
                    "output": result
                })
                logger.info(f"Step {step_id} - Saved result with id: {step['id']}")
            
            return result
            
        # 处理并行步骤
        elif step_type == "parallel":
            # 创建上下文
            context = {
                "input_text": input_text,
                "parameters": self.context.get("parameters", {}),
                "outputs": {
                    result["id"]: result["output"]
                    for result in self.context["steps_results"]
                    if "id" in result
                }
            }
            
            # 执行并行步骤
            results = await self.parallel_executor.execute(step, input_text, context)
            
            # 如果步骤有ID，保存结果
            if "id" in step:
                self.context["steps_results"].append({
                    "id": step["id"],
                    "output": results
                })
                logger.info(f"Step {step_id} - Saved parallel results with id: {step['id']}")
            
            # 返回结果列表的最后一个结果作为输出
            return results[-1] if results else input_text
            
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