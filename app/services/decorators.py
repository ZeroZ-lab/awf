import functools
import time
import asyncio
from typing import Any, Callable, Type, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def retry_async(
    retries: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff_factor: float = 2.0
) -> Callable:
    """异步重试装饰器
    
    Args:
        retries: 最大重试次数
        delay: 初始延迟时间（秒）
        exceptions: 需要重试的异常类型
        backoff_factor: 退避因子，每次重试延迟时间会乘以这个因子
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == retries:
                        logger.error(f"Final retry attempt failed: {str(e)}")
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{retries} failed: {str(e)}. "
                        f"Retrying in {current_delay} seconds..."
                    )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
            
            raise last_exception
        return wrapper
    return decorator

def monitor_performance(service: str, operation: str) -> Callable:
    """性能监控装饰器
    
    Args:
        service: 服务名称
        operation: 操作名称
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Performance: {service}.{operation} completed in {duration:.3f}s"
                )
                return result
            except Exception as e:
                logger.error(
                    f"Error in {service}.{operation}: {type(e).__name__}: {str(e)}"
                )
                raise
        return wrapper
    return decorator

def cache_result(
    ttl: Optional[float] = None,
    max_size: int = 100
) -> Callable:
    """结果缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒），None 表示永不过期
        max_size: 最大缓存条目数
    """
    cache = {}
    cache_times = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 生成缓存键
            key = str((args, frozenset(kwargs.items())))
            
            # 检查缓存是否过期
            current_time = time.time()
            if key in cache:
                cache_time = cache_times[key]
                if ttl is None or (current_time - cache_time) < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache[key]
            
            # 获取新结果
            result = await func(*args, **kwargs)
            
            # 更新缓存
            cache[key] = result
            cache_times[key] = current_time
            
            # 如果超过最大大小，删除最旧的条目
            if len(cache) > max_size:
                oldest_key = min(cache_times, key=cache_times.get)
                del cache[oldest_key]
                del cache_times[oldest_key]
                logger.debug(f"Cache cleanup for {func.__name__}, removed oldest entry")
            
            return result
        return wrapper
    return decorator 