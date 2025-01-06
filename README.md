![rn0krugs5skb8frvfxh5](https://github.com/user-attachments/assets/9be88b3a-a508-40ed-bcab-b7688adf79a5)

# AI Workflow Framework

A flexible AI workflow framework that supports configurable workflow definition and execution.

## Workflow Configuration Guide

Workflows are defined in YAML format, supporting conditional branching, model invocation, and other features. Below is the complete configuration guide.

### Basic Structure

```yaml
workflow_id: unique_workflow_id  # Unique identifier for the workflow
name: Workflow Name             # Name of the workflow
description: Description        # Workflow description
version: "1.0"                 # Version number

parameters:                     # Workflow parameter definitions
  param_name:                  # Parameter name
    type: string              # Parameter type: string/integer/float/boolean
    default: "default_value"  # Default value
    required: false           # Whether required
    description: "Parameter description"  # Parameter description

steps:                         # Workflow step definitions
  - type: step_type           # Step type
    id: step_id               # Step identifier
    description: "Step description"  # Step description
    # Other step-specific configurations...
```

### Parameter Configuration

Parameters support the following configuration options:

```yaml
parameters:
  language:
    type: string              # Parameter type
    default: "en"            # Default value
    required: false          # Whether required
    description: "Output language"  # Parameter description
  max_length:
    type: integer
    default: 500
    required: false
    description: "Maximum length limit"
```

### Step Types

#### 1. LLM Step

Used to call language models for text generation.

```yaml
- type: llm
  id: step_id                # Unique step identifier
  description: "Step description"  # Step description
  model: model_id           # Model identifier
  prompt_template: |        # Prompt template
    Write your prompt here
    Use {input_text} to reference input
    Use $param(param_name) to reference parameters
    Use $output(step_id) to reference other step outputs
  temperature: 0.7         # Temperature parameter
  max_tokens: 1000        # Maximum generation length
```

#### 2. Conditional Step

Used to implement conditional branching logic.

```yaml
- type: if
  description: "Condition description"
  condition: "$length(step_id) > $param(max_length)"  # Condition expression
  then:                    # Steps to execute when condition is true
    - type: llm
      # ... step configuration
  else:                   # Steps to execute when condition is false
    - type: llm
      # ... step configuration
```

### Template Syntax

The following special syntax is supported in prompt templates:

1. Parameter References:
```
$param(parameter_name)    # Reference workflow parameters
```

2. Output References:
```
$output(step_id)         # Reference other step outputs
```

3. Function Calls:
```
$length(step_id)         # Get text length
$if(condition, value1, value2)  # Conditional expression
```

4. Input References:
```
{input_text}             # Reference current step input text
```

### Condition Expressions

Condition steps support the following expressions:

1. Comparison Operations:
```yaml
condition: "$length(step_id) > $param(max_length)"  # Greater than
condition: "$length(step_id) < $param(max_length)"  # Less than
condition: "$length(step_id) == $param(max_length)" # Equal to
```

2. Special Conditions:
```yaml
condition: "has_summary"  # Check if specific step output exists
```

### Complete Example

```yaml
workflow_id: text_processing
name: Text Processing Workflow
description: Process and optimize text content
version: "1.0"

parameters:
  language:
    type: string
    default: "en"
    required: false
    description: "Output language"
  style:
    type: string
    default: "professional"
    required: false
    description: "Output style"
  max_length:
    type: integer
    default: 500
    required: false
    description: "Maximum length limit"

steps:
  - type: llm
    id: initial_response
    description: "Generate initial response"
    model: openrouter-deepseek
    prompt_template: |
      Please respond to the following content using $param(style) tone in $param(language):
      {input_text}
    temperature: 0.7
    max_tokens: 1000

  - type: if
    description: "Decide whether to summarize based on text length"
    condition: "$length(initial_response) > $param(max_length)"
    then:
      - type: llm
        id: summary
        description: "Generate summary"
        model: openrouter-deepseek
        prompt_template: |
          Please summarize the following content while keeping key points:
          $output(initial_response)
        temperature: 0.3
        max_tokens: 200
    else:
      - type: llm
        id: optimization
        description: "Optimize expression"
        model: openrouter-deepseek
        prompt_template: |
          Please optimize the expression of the following content for clarity and conciseness:
          $output(initial_response)
        temperature: 0.5
        max_tokens: 300

  - type: llm
    id: final_polish
    description: "Final polish"
    model: openrouter-deepseek
    prompt_template: |
      Please polish the following content to ensure natural and fluent language:
      $output($if(has_summary, summary, optimization))
    temperature: 0.4
    max_tokens: 500
```

## Important Notes

1. All step `id`s must be unique within the workflow
2. Parameter references must use defined parameter names
3. Output references must use IDs of previously executed steps
4. Condition expressions should maintain clear logic and avoid complex nesting
5. Prompt templates should be clear and unambiguous

## Best Practices

1. Provide clear descriptions for each step
2. Set reasonable parameter default values
3. Use appropriate temperature parameters to control output randomness
4. Set suitable maximum generation lengths as needed
5. Pay attention to dependencies between steps
6. Maintain clear workflow structure and avoid overly complex logic

[中文文档](README_ZH.md)