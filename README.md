![rn0krugs5skb8frvfxh5](https://github.com/user-attachments/assets/9be88b3a-a508-40ed-bcab-b7688adf79a5)

# AI Workflow Service

AI Workflow Service is a flexible AI workflow orchestration service that supports the combination of multiple AI models and tools.

## Features

### Workflow System
- Support for multi-step serial execution
- Rich conditional control support
  - if-else conditional branching
  - switch-case branching
  - match pattern matching
- Error handling and retry mechanisms
- Context passing and result optimization

Coming soon:
- Parallel task execution
- Loop execution
- Nested workflows
- Agents as workflow nodes

### Conditional Execution Examples

#### 1. if-else Conditional Branching
```yaml
steps:
  - type: if
    condition: "len(input_text) > 100"  # Supports expressions
    then:  # Execute when condition is true
      - type: llm
        model: openrouter-deepseek
        prompt_template: "This is a long text, please summarize: {input_text}"
    else:  # Execute when condition is false
      - type: llm
        model: openrouter-deepseek
        prompt_template: "This is a short text, please process directly: {input_text}"
```

#### 2. switch-case Branching
```yaml
steps:
  - type: switch
    value: "status_code"  # Value to match
    cases:
      - value: "200"
        steps:
          - type: llm
            model: openrouter-deepseek
            prompt_template: "Process successful response: {input_text}"
      - value: "404"
        steps:
          - type: llm
            model: openrouter-deepseek
            prompt_template: "Process not found error: {input_text}"
    default:  # Default case
      - type: llm
        model: openrouter-deepseek
        prompt_template: "Process other cases: {input_text}"
```

#### 3. match Pattern Matching
```yaml
steps:
  - type: match
    value: "response.status"
    conditions:
      - when: "value >= 200 and value < 300"
        steps:
          - type: llm
            model: openrouter-deepseek
            prompt_template: "Process successful response: {input_text}"
      - when: "value >= 400 and value < 500"
        steps:
          - type: llm
            model: openrouter-deepseek
            prompt_template: "Process client error: {input_text}"
    default:
      - type: llm
        model: openrouter-deepseek
        prompt_template: "Process other cases: {input_text}"
```

### AI Model Integration
- OpenAI API support
- OpenRouter API support
- Flexible model configuration system

### Tool System
- Custom tool development support
- Extensible tool registration mechanism

### System Features
- Complete logging
- Configuration validation
- Error handling
- API documentation

## Quick Start

### 1. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .

# Install development dependencies (optional)
pip install pytest==8.3.4 pytest-asyncio==0.25.1 pytest-mock==3.14.0
```

### 2. Configuration
```bash
# Copy environment variable template
cp .env.example .env

# Edit .env file, set necessary configuration items:
# - OPENAI_API_KEY
# - OPENROUTER_API_KEY
# - LOG_LEVEL
```

### 3. Start Service
```bash
# Development mode
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Run Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_api.py

# Run specific test case
pytest tests/test_api.py::test_run_workflow
```

## Configuration Files

### Workflow Configuration
Location: `app/instances/workflows/*.yaml`
```yaml
workflow_id: example_workflow
name: Example Workflow
description: Workflow description
version: "1.0"
steps:
  - type: llm
    model: openrouter-deepseek
    prompt_template: |
      Please process the following content: {input_text}
```

### Model Configuration
Location: `app/instances/models.yaml`
```yaml
models:
  - model_id: openrouter-deepseek
    name: DeepSeek Chat
    type: openrouter
    params:
      model_name: deepseek-chat
      api_key_env: OPENROUTER_API_KEY
```

### Tool Configuration
Location: `app/instances/tools.yaml`
```yaml
tools:
  - name: SearchTool
    description: Search tool
    class_name: SearchTool
    module: app.tools.search
```

## API Endpoints

### Execute Workflow
```bash
POST /api/v1/workflows/{workflow_id}/run
Content-Type: application/json

{
    "input_text": "Content to process",
    "parameters": {
        "max_length": 100
    }
}
```

Response format:
```json
{
    "result": "Processing result"
}
```

Response status codes:
- 200: Success
- 404: Workflow not found
- 422: Invalid request parameters
- 500: Internal server error

### Stream Workflow Execution
```bash
POST /api/v1/workflows/{workflow_id}/run/stream
Content-Type: application/json

{
    "input_text": "Content to process",
    "parameters": {
        "max_length": 100
    }
}
```

Response format:
```
data: {"type": "step_start", "step": "Generate initial response", "timestamp": "..."}

data: {"type": "step_complete", "step": "Generate initial response", "result": "...", "timestamp": "..."}

data: {"type": "complete", "result": "Final result", "timestamp": "..."}
```

### Health Check
```bash
GET /health

Response:
{
    "status": "ok"
}
```

## Development Guide

### Adding New Tools
1. Create new tool class in `app/services/tools/`
2. Inherit from `BaseTool` class
3. Implement `__call__` method
4. Register tool in `app/instances/tools.yaml`

### Error Handling
The system implements multi-layer error handling:
1. API Layer: Unified error response format
2. Workflow Layer: Step execution error handling
3. Model Layer: API call retry and error handling
4. Configuration Layer: Configuration validation and error prompts

[中文文档](README_ZH.md)