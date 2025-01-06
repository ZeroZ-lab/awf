
![rn0krugs5skb8frvfxh5](https://github.com/user-attachments/assets/9be88b3a-a508-40ed-bcab-b7688adf79a5)

# AI Workflow Service

AI Workflow Service 是一个灵活的 AI 工作流编排服务，支持多种 AI 模型和工具的组合调用。

## 特性

### 工作流系统
- 支持多步骤串行执行
- 支持丰富的条件控制
  - if-else 条件分支
  - switch-case 分支
  - match 模式匹配
- 支持错误处理和重试机制
- 支持上下文传递和结果优化

即将推出的功能：
- 并行任务执行
- 循环执行
- 嵌套工作流
- Agent 作为工作流节点

### 条件执行示例

#### 1. if-else 条件分支
```yaml
steps:
  - type: if
    condition: "len(input_text) > 100"  # 支持表达式
    then:  # 条件为真时执行
      - type: llm
        model: openrouter-deepseek
        prompt_template: "这是一段长文本，请总结：{input_text}"
    else:  # 条件为假时执行
      - type: llm
        model: openrouter-deepseek
        prompt_template: "这是一段短文本，请直接处理：{input_text}"
```

#### 2. switch-case 分支
```yaml
steps:
  - type: switch
    value: "status_code"  # 要匹配的值
    cases:
      - value: "200"
        steps:
          - type: llm
            model: openrouter-deepseek
            prompt_template: "处理成功响应：{input_text}"
      - value: "404"
        steps:
          - type: llm
            model: openrouter-deepseek
            prompt_template: "处理未找到错误：{input_text}"
    default:  # 默认情况
      - type: llm
        model: openrouter-deepseek
        prompt_template: "处理其他情况：{input_text}"
```

#### 3. match 模式匹配
```yaml
steps:
  - type: match
    value: "response.status"
    conditions:
      - when: "value >= 200 and value < 300"
        steps:
          - type: llm
            model: openrouter-deepseek
            prompt_template: "处理成功响应：{input_text}"
      - when: "value >= 400 and value < 500"
        steps:
          - type: llm
            model: openrouter-deepseek
            prompt_template: "处理客户端错误：{input_text}"
    default:
      - type: llm
        model: openrouter-deepseek
        prompt_template: "处理其他情况：{input_text}"
```

### AI 模型集成
- 支持 OpenAI API
- 支持 OpenRouter API
- 灵活的模型配置系统

### 工具系统
- 支持自定义工具开发
- 可扩展的工具注册机制

### 系统功能
- 完整的日志记录
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
pip install -e .

# 安装开发依赖（可选）
pip install pytest==8.3.4 pytest-asyncio==0.25.1 pytest-mock==3.14.0
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

### 4. 运行测试
```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_api.py

# 运行特定测试用例
pytest tests/test_api.py::test_run_workflow
```

## 配置文件

### 工作流配置
位置：`app/instances/workflows/*.yaml`
```yaml
workflow_id: example_workflow
name: 示例工作流
description: 工作流描述
version: "1.0"
steps:
  - type: llm
    model: openrouter-deepseek
    prompt_template: |
      请处理以下内容：{input_text}
```

### 模型配置
位置：`app/instances/models.yaml`
```yaml
models:
  - model_id: openrouter-deepseek
    name: DeepSeek Chat
    type: openrouter
    params:
      model_name: deepseek-chat
      api_key_env: OPENROUTER_API_KEY
```

### 工具配置
位置：`app/instances/tools.yaml`
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
POST /api/v1/workflows/{workflow_id}/run
Content-Type: application/json

{
    "input_text": "需要处理的内容",
    "parameters": {
        "max_length": 100
    }
}
```

响应格式：
```json
{
    "result": "处理结果"
}
```

响应状态码：
- 200: 成功
- 404: 工作流不存在
- 422: 请求参数无效
- 500: 服务器内部错误

### 流式执行工作流
```bash
POST /api/v1/workflows/{workflow_id}/run/stream
Content-Type: application/json

{
    "input_text": "需要处理的内容",
    "parameters": {
        "max_length": 100
    }
}
```

响应格式：
```
data: {"type": "step_start", "step": "生成初始回复", "timestamp": "..."}

data: {"type": "step_complete", "step": "生成初始回复", "result": "...", "timestamp": "..."}

data: {"type": "complete", "result": "最终结果", "timestamp": "..."}
```

### 健康检查
```bash
GET /health

响应：
{
    "status": "ok"
}
```

## 开发指南

### 添加新工具
1. 在 `app/services/tools/` 创建新工具类
2. 继承 `BaseTool` 类
3. 实现 `__call__` 方法
4. 在 `app/instances/tools.yaml` 注册工具

### 错误处理
系统实现了多层错误处理机制：
1. API 层：统一的错误响应格式
2. 工作流层：步骤执行错误处理
3. 模型层：API 调用重试和错误处理
4. 配置层：配置验证和错误提示
