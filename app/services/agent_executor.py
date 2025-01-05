from typing import List, Dict, Any
from app.tools.base import BaseTool
from app.services.model_manager import models

def run_react_agent(input_text: str, available_tools: List[BaseTool], prompt_template: str, agent_config: Dict[str, Any]) -> str:
    history = ""
    model_id = agent_config.get("llm_model")
    llm_model = models.get(model_id)
    if not llm_model:
        raise ValueError(f"Model not found: {model_id}")

    while True:
        llm_output = react_reasoning(input_text, available_tools, prompt_template, history, llm_model)
        print(f"LLM 输出: {llm_output}")

        if "最终答案:" in llm_output:
            answer = llm_output.split("最终答案:")[1].strip()
            print(f"最终答案: {answer}")
            return answer

        action_result = react_action(llm_output, available_tools)
        if action_result:
            history += f"\n用户：{input_text}\nAI：{llm_output}\n工具结果：{action_result}"
            print(f"工具结果: {action_result}")
        else:
            history += f"\n用户：{input_text}\nAI：{llm_output}"
        input_text = "基于之前的回复，继续你的思考并完成任务。"

def react_reasoning(input_text: str, tools: List[BaseTool], prompt_template: str, history: str, llm_model) -> str:
    formatted_tools = [{"name": tool.name, "description": tool.description} for tool in tools]
    prompt = prompt_template.format(
        input_text=input_text,
        tools="\n".join([f"- {t['name']}: {t['description']}" for t in formatted_tools]),
        history=history
    )
    return llm_model.generate_text(prompt)

def react_action(llm_output: str, available_tools: List[BaseTool]) -> str:
    if "行动:" not in llm_output:
        return None
        
    action_part = llm_output.split("行动:")[1].split("\n")[0].strip()
    if "," not in action_part:
        return None
        
    tool_name = action_part.split(",")[0].strip()
    tool_input = ",".join(action_part.split(",")[1:]).strip()
    
    for tool in available_tools:
        if tool.name == tool_name:
            try:
                return tool(tool_input) if tool_input else tool()
            except Exception as e:
                return f"工具执行错误: {str(e)}"
                
    return f"未找到工具: {tool_name}" 