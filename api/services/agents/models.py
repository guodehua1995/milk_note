from typing import Literal, TypedDict

class AgentClassification(TypedDict):
    '''
        智能体分类
    '''
    intent: Literal["just_talk", "search", "tools_use", "plan_node"]
    dialog_summary: str | None

class AgentPlan(TypedDict):
    '''
        智能体计划
    '''
    step: int
    intent: Literal["plan_llm_call", "plan_tools_use", "plan_decomposition"]
    title: str | None
    content: str | None
    result: str | None
    tools: list[str] | None
    status: Literal["wait","success", "failed"] | None

class AgentPlans(TypedDict):
    '''
        智能体计划列表
    '''
    plans: list[AgentPlan]
    current_step: int | None
    status: Literal["doing","success", "failed"]

class ToolChoice(TypedDict):
    '''
        工具选择
    '''
    tools: list[str] | None
    work_flow: str | None

class PlanLLMCall(TypedDict):
    '''
        计划LLM调用
    '''
    prompt: str | None
    response: str | None

class SearchType(TypedDict):
    '''
        搜索类型
    '''
    search_type: Literal["rag_only", "web_search_only", "rag_web_search"]
    search_content: str | None