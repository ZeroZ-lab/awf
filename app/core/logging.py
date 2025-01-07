import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    """配置日志系统"""
    # 从环境变量获取配置
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "app.log")
    log_dir = os.getenv("LOG_DIR", "logs")
    log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 完整的日志文件路径
    log_file_path = log_path / log_file

    # 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            # 文件处理器，支持日志轮转
            RotatingFileHandler(
                log_file_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            ),
            # 控制台处理器
            logging.StreamHandler()
        ]
    )

    # 设置第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured. Log file: {log_file_path}") 