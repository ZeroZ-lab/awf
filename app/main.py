from fastapi import FastAPI
from app.api.v1 import workflows
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(
    title="AI Workflow Service",
    description="AI 工作流编排服务",
    version="1.0.0"
)

# 注册路由
app.include_router(workflows.router)

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy"} 