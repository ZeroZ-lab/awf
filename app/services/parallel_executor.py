from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ParallelExecutor:
    """并行执行器，用于处理并行任务"""
    
    def __init__(self, step_executor):
        """
        初始化并行执行器
        
        Args:
            step_executor: 用于执行单个步骤的执行器函数
        """
        self.step_executor = step_executor
        
    async def execute(self, step: Dict[str, Any], input_text: str, context: Dict[str, Any]) -> List[str]:
        """
        执行并行步骤
        
        Args:
            step: 步骤配置
            input_text: 输入文本
            context: 执行上下文
            
        Returns:
            List[str]: 所有并行任务的执行结果列表
        """
        parallel_steps = step.get("steps", [])
        if not parallel_steps:
            raise ValueError("No steps provided for parallel execution")
            
        # 创建任务列表
        tasks = []
        for parallel_step in parallel_steps:
            # 为每个并行步骤创建独立的上下文副本
            step_context = context.copy()
            task = asyncio.create_task(
                self._execute_parallel_step(parallel_step, input_text, step_context)
            )
            tasks.append(task)
            
        # 等待所有任务完成
        try:
            results = await asyncio.gather(*tasks)
            return results
        except Exception as e:
            logger.error(f"Error in parallel execution: {str(e)}")
            raise
            
    async def _execute_parallel_step(
        self, 
        step: Dict[str, Any], 
        input_text: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        执行单个并行步骤
        
        Args:
            step: 步骤配置
            input_text: 输入文本
            context: 执行上下文
            
        Returns:
            str: 步骤执行结果
        """
        try:
            # 记录开始时间
            start_time = datetime.now()
            
            # 执行步骤
            result = await self.step_executor(step, input_text)
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Parallel step executed in {execution_time:.2f} seconds")
            
            return result
        except Exception as e:
            logger.error(f"Error executing parallel step: {str(e)}")
            raise 