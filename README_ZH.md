# AI 工作流框架

一个灵活的 AI 工作流框架，支持配置化的工作流定义和执行。

## 工作流配置指南

工作流使用 YAML 格式定义，支持条件分支、模型调用等功能。以下是完整的配置指南。

### 基本结构

```yaml
workflow_id: unique_workflow_id  # 工作流唯一标识符
name: Workflow Name             # 工作流名称
description: Description        # 工作流描述
version: "1.0"                 # 版本号

parameters:                     # 工作流参数定义
  param_name:                  # 参数名称
    type: string              # 参数类型：string/integer/float/boolean
    default: "default_value"  # 默认值
    required: false           # 是否必需
    description: "参数说明"    # 参数描述

steps:                         # 工作流步骤定义
  - type: step_type           # 步骤类型
    id: step_id               # 步骤标识符
    description: "步骤说明"    # 步骤描述
    # 其他步骤特定配置...
```

### 参数配置

参数支持以下配置选项：

```yaml
parameters:
  language:
    type: string              # 参数类型
    default: "zh"            # 默认值
    required: false          # 是否必需
    description: "输出语言"   # 参数说明
  max_length:
    type: integer
    default: 500
    required: false
    description: "最大长度限制"
```

### 步骤类型

#### 1. LLM 步骤

用于调用语言模型生成文本。

```yaml
- type: llm
  id: step_id                # 步骤唯一标识符
  description: "步骤说明"     # 步骤描述
  model: model_id           # 模型标识符
  prompt_template: |        # 提示模板
    在这里编写提示词
    可以使用 {input_text} 引用输入
    可以使用 $param(param_name) 引用参数
    可以使用 $output(step_id) 引用其他步骤的输出
  temperature: 0.7         # 温度参数
  max_tokens: 1000        # 最大生成长度
```

#### 2. 条件步骤

用于实现条件分支逻辑。

```yaml
- type: if
  description: "条件判断说明"
  condition: "$length(step_id) > $param(max_length)"  # 条件表达式
  then:                    # 条件为真时执行的步骤
    - type: llm
      # ... 步骤配置
  else:                   # 条件为假时执行的步骤
    - type: llm
      # ... 步骤配置
```

### 模板语法

在提示模板中支持以下特殊语法：

1. 参数引用：
```
$param(parameter_name)    # 引用工作流参数
```

2. 输出引用：
```
$output(step_id)         # 引用其他步骤的输出
```

3. 函数调用：
```
$length(step_id)         # 获取文本长度
$if(condition, value1, value2)  # 条件表达式
```

4. 输入引用：
```
{input_text}             # 引用当前步骤的输入文本
```

### 条件表达式

条件步骤中的条件表达式支持：

1. 比较操作：
```yaml
condition: "$length(step_id) > $param(max_length)"  # 大于
condition: "$length(step_id) < $param(max_length)"  # 小于
condition: "$length(step_id) == $param(max_length)" # 等于
```

2. 特殊条件：
```yaml
condition: "has_summary"  # 检查是否存在特定步骤的输出
```

### 完整示例

```yaml
workflow_id: text_processing
name: 文本处理工作流
description: 处理和优化文本内容
version: "1.0"

parameters:
  language:
    type: string
    default: "zh"
    required: false
    description: "输出语言"
  style:
    type: string
    default: "professional"
    required: false
    description: "输出风格"
  max_length:
    type: integer
    default: 500
    required: false
    description: "最大长度限制"

steps:
  - type: llm
    id: initial_response
    description: "生成初始回复"
    model: openrouter-deepseek
    prompt_template: |
      请用$param(style)的语气，使用$param(language)回复以下内容：
      {input_text}
    temperature: 0.7
    max_tokens: 1000

  - type: if
    description: "根据生成文本长度决定是否需要总结"
    condition: "$length(initial_response) > $param(max_length)"
    then:
      - type: llm
        id: summary
        description: "生成摘要"
        model: openrouter-deepseek
        prompt_template: |
          请对以下内容进行总结，保持要点完整：
          $output(initial_response)
        temperature: 0.3
        max_tokens: 200
    else:
      - type: llm
        id: optimization
        description: "优化表达"
        model: openrouter-deepseek
        prompt_template: |
          请优化以下内容的表达，使其更加清晰简洁：
          $output(initial_response)
        temperature: 0.5
        max_tokens: 300

  - type: llm
    id: final_polish
    description: "最终润色"
    model: openrouter-deepseek
    prompt_template: |
      请对以下内容进行润色，确保语言流畅自然：
      $output($if(has_summary, summary, optimization))
    temperature: 0.4
    max_tokens: 500
```

## 注意事项

1. 所有步骤的 `id` 必须在工作流中唯一
2. 参数引用必须使用已定义的参数名
3. 输出引用必须使用已执行步骤的 id
4. 条件表达式应确保逻辑清晰，避免复杂嵌套
5. 提示模板应清晰明确，避免歧义

## 最佳实践

1. 为每个步骤提供清晰的描述
2. 合理设置参数默认值
3. 使用适当的温度参数控制输出的随机性
4. 根据需要设置合适的最大生成长度
5. 注意步骤之间的依赖关系
6. 保持工作流结构清晰，避免过度复杂的逻辑

[English Documentation](README.md)
