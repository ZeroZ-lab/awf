# AI Workflow Service

AI Workflow Service 是一个灵活的 AI 工作流编排服务，支持多种 AI 模型和工具的组合调用。

## 特性

### 工作流系统
- 支持多步骤串行执行
- 支持嵌套工作流
- 支持 Agent 作为工作流节点
- 支持上下文传递和结果优化
- 支持条件分支执行
- 支持并行任务执行
- 支持循环执行
- 支持错误处理和重试机制

### AI 模型集成
- 支持 OpenAI API
- 支持 OpenRouter API
- 支持本地模型部署
- 灵活的模型配置系统

### 工具系统
- 内置搜索工具
- 内置计算工具
- 支持工作流作为工具
- 可扩展的工具注册机制

### 系统功能
- 完整的日志记录
- 性能监控
- 配置验证
- 错误处理
- API 文档

## 快速开始

### 1. 环境准备
```bash
# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e ".[dev]"
```

### 2. 配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置必要的配置项：
# - OPENAI_API_KEY
# - OPENROUTER_API_KEY
# - LOG_LEVEL
```

### 3. 启动服务
```bash
# 开发模式
uvicorn app.main:app --reload --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 配置文件

### 工作流配置
位置：`config/workflows/*.yaml`
```yaml
workflow_id: example_workflow
name: 示例工作流
steps:
  - type: llm
    model: openrouter-deepseek
    prompt_template: |
      请处理以下内容：{input_text}
```

### 模型配置
位置：`config/models.yaml`
```yaml
models:
  - model_id: openrouter-deepseek
    name: DeepSeek Chat
    type: openrouter
    params:
      model_name: deepseek-chat
```

### 工具配置
位置：`config/tools.yaml`
```yaml
tools:
  - name: SearchTool
    description: 搜索工具
    class_name: SearchTool
    module: app.tools.search
```

## API 接口

### 执行工作流
```bash
POST /api/v1/execute
Content-Type: application/json

{
    "workflow_id": "example_workflow",
    "input_text": "需要处理的内容"
}
```

### 健康检查
```bash
GET /health
```

## 开发指南

### 添加新工具
1. 在 `app/tools/` 创建新工具类
2. 继承 `BaseTool` 类
3. 实现 `__call__` 方法
4. 在 `config/tools.yaml` 注册工具

### 添加新模型
1. 在 `app/services/providers/` 创建新的 provider
2. 实现必要的接口方法
3. 在 `config/models.yaml` 添加配置

### 创建新工作流
1. 在 `config/workflows/` 创建新的 YAML 文件
2. 定义工作流步骤
3. 支持的步骤类型：
   - llm: 调用语言模型
   - agent: 执行智能体
   - workflow: 调用其他工作流
   - parallel: 并行执行
   - if: 条件分支
   - foreach: 循环执行

## 目录结构
```
app/
├── api/            # API 接口
├── core/           # 核心功能
├── models/         # 数据模型
├── services/       # 服务层
├── tools/          # 工具集
└── main.py         # 入口文件

config/
├── agents/         # Agent 配置
├── workflows/      # 工作流配置
├── models.yaml     # 模型配置
└── tools.yaml      # 工具配置

tests/              # 测试文件
```

## 许可证

MIT License
