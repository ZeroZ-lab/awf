# AI Workflow Service

AI Workflow Service 是一个灵活的 AI 工作流编排服务，支持多种 AI 模型和工具的组合调用。

## 特性

### 工作流系统
- 支持多步骤串行执行
- 支持嵌套工作流
- 支持 Agent 作为工作流节点
- 支持上下文传递和结果优化
- 支持丰富的条件控制
  - if-else 条件分支
  - switch-case 分支
  - match 模式匹配
- 支持并行任务执行
- 支持循环执行
- 支持错误处理和重试机制

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

### 错误处理和重试
```yaml
steps:
  - type: llm
    model: openrouter-deepseek
    prompt_template: "分析文本：{input_text}"
    error_handling:
      retry:
        times: 3        # 最多重试3次（总共执行4次）
        interval: 2     # 每次重试间隔2秒
      fallback:         # 如果重试全部失败，执行这些备选步骤
        steps:
          - type: llm
            model: openai-gpt-3.5-turbo-instruct
            prompt_template: "使用备选模型分析：{input_text}"
```

### 并行执行
```yaml
steps:
  - type: parallel
    tasks:
      - type: llm
        model: openrouter-deepseek
        prompt_template: "分析观点：{input_text}"
      - type: llm
        model: openai-gpt-3.5-turbo-instruct
        prompt_template: "提取关键词：{input_text}"
```

### 循环执行
```yaml
steps:
  - type: foreach
    items: "{data_list}"    # 要遍历的数据列表
    item_name: item         # 当前项在上下文中的变量名
    steps:
      - type: llm
        model: openrouter-deepseek
        prompt_template: "处理当前项：{item}"
```

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
位置：`app/instances/workflows/*.yaml`
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
位置：`app/instances/models.yaml`
```yaml
models:
  - model_id: openrouter-deepseek
    name: DeepSeek Chat
    type: openrouter
    params:
      model_name: deepseek-chat
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
    "input_text": "需要处理的内容"
}
```

响应格式：
```json
{
    "result": "处理结果",
    "execution_time": 1.234,
    "status": "success"
}
```

### 健康检查
```bash
GET /health
```

## 开发指南

### 添加新工具
1. 在 `app/services/tools/` 创建新工具类
2. 继承 `BaseTool` 类
3. 实现 `__call__` 方法
4. 在 `app/instances/tools.yaml` 注册工具

### 添加新模型
1. 在 `app/services/providers/` 创建新的 provider
2. 实现必要的接口方法
3. 在 `app/instances/models.yaml` 添加配置

### 创建新工作流
1. 在 `app/instances/workflows/` 创建新的 YAML 文件
2. 定义工作流步骤
3. 支持的步骤类型：

   - `llm`: 调用语言模型
     ```yaml
     - type: llm
       model: openrouter-deepseek
       prompt_template: "提示词模板"
     ```

   - `agent`: 执行智能体
     ```yaml
     - type: agent
       agent_id: summary_agent
       task: "任务描述"
     ```

   - `workflow`: 调用其他工作流
     ```yaml
     - type: workflow
       workflow_id: nested_workflow
     ```

   - `parallel`: 并行执行多个步骤
     ```yaml
     - type: parallel
       tasks:
         - type: llm
           model: openrouter-deepseek
           prompt_template: "提示词1"
         - type: agent
           agent_id: summary_agent
           task: "任务2"
     ```

   - `if`: 条件分支执行
     ```yaml
     - type: if
       condition: "{data} > 100"
       then:
         - type: llm
           model: openrouter-deepseek
           prompt_template: "条件为真时执行"
       else:
         - type: agent
           agent_id: summary_agent
           task: "条件为假时执行"
     ```

   - `foreach`: 循环执行
     ```yaml
     - type: foreach
       items: "{data_list}"
       item_name: item
       steps:
         - type: llm
           model: openrouter-deepseek
           prompt_template: "处理当前项: {item}"
     ```

4. 错误处理配置（可选）：
   ```yaml
   - type: llm
     model: openrouter-deepseek
     prompt_template: "..."
     error_handling:
       retry:
         times: 3
         interval: 1
       fallback:
         steps:
           - type: llm
             model: openai-gpt-3.5-turbo-instruct
             prompt_template: "备选方案"
   ```

## 目录结构
```
app/
├── api/            # API 接口
├── core/           # 核心功能
├── models/         # 数据模型
├── services/       # 服务层
│   ├── providers/  # 模型提供者
│   └── tools/      # 工具实现类
├── instances/      # 实例化配置
│   ├── agents/     # Agent 实例配置
│   ├── workflows/  # 工作流实例配置
│   ├── models.yaml # 模型实例配置
│   └── tools.yaml  # 工具实例配置
└── main.py         # 入口文件

tests/              # 测试文件
```

## 许可证

MIT License
