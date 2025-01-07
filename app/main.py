from fastapi import FastAPI
from app.api.v1 import workflows
from app.services.model_manager import models
from app.core.logging import setup_logging
import logging

# 设置日志配置
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Workflow Framework")

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("Starting AI Workflow Framework...")
    logger.info("Initializing model manager...")
    await models.initialize()
    logger.info("Model manager initialized")

app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"]) 