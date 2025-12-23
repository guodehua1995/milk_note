from api.core import settings
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, ToolMessage, HumanMessage, AnyMessage
from typing_extensions import TypedDict, Annotated
from typing import Literal, List
from langgraph.graph import StateGraph, START, END
import operator
import os
from langchain.tools import tool


@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b


# 定义工具列表
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}


class MessagesState(TypedDict):
    """消息状态"""
    messages: Annotated[List[AnyMessage], operator.add]
    llm_calls: int


class AgentService:
    """LangGraph Agent 核心服务
    
    负责创建和运行 LangGraph Agent，处理用户请求
    """
    
    def __init__(self):
        """初始化 Agent 服务，创建 LLM 实例和工具绑定"""
        # 创建 LLM 实例
        self.llm = ChatOpenAI(
            api_key=os.environ.get(settings.MILK_NOTE_API_KEY),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            temperature=0.7
        )
        
        # 绑定工具到 LLM
        self.model_with_tools = self.llm.bind_tools(tools)
        
        # 创建 Agent Graph
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """创建 LangGraph Agent 图"""
        
        def llm_call(state: dict):
            """LLM调用节点"""
            return {
                "messages": [
                    self.model_with_tools.invoke(
                        [
                            SystemMessage(
                                content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                            )
                        ]
                        + state["messages"]
                    )
                ],
                "llm_calls": state.get('llm_calls', 0) + 1
            }
        
        def tool_node(state: dict):
            """工具执行节点"""
            result = []
            for tool_call in state["messages"][-1].tool_calls:
                tool = tools_by_name[tool_call["name"]]
                observation = tool.invoke(tool_call["args"])
                result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
            return {"messages": result}
        
        def should_continue(state: MessagesState) -> Literal["tool_node", END]:
            """条件分支节点，判断是否需要继续执行工具"""
            messages = state["messages"]
            last_message = messages[-1]
            
            if last_message.tool_calls:
                return "tool_node"
            return END
        
        # 构建工作流
        agent_builder = StateGraph(MessagesState)
        
        # 添加节点
        agent_builder.add_node("llm_call", llm_call)
        agent_builder.add_node("tool_node", tool_node)
        
        # 构建节点关系
        agent_builder.add_edge(START, "llm_call")
        agent_builder.add_conditional_edges(
            "llm_call",
            should_continue,
            ["tool_node", END]
        )
        agent_builder.add_edge("tool_node", "llm_call")
        
        # 编译 Agent
        return agent_builder.compile()
    
    def run_agent(self, prompt: str, history: List[AnyMessage] = None):
        """运行 Agent 处理请求
        
        Args:
            prompt: 用户输入的提示词
            history: 历史消息列表
            
        Returns:
            生成器，产生流式响应
        """
        # 准备初始消息
        initial_messages = history or []
        initial_messages.append(HumanMessage(content=prompt))
        
        # 运行 Agent 图，支持流式输出
        for event in self.agent.stream({
            "messages": initial_messages,
            "llm_calls": 0
        }):
            # 处理流式输出
            for node, output in event.items():
                if node == "llm_call":
                    # 获取最新的消息
                    last_message = output["messages"][-1]
                    if not last_message.tool_calls:  # 如果不是工具调用，返回给用户
                        yield last_message.content
    
    def invoke_agent(self, prompt: str, history: List[AnyMessage] = None):
        """同步调用 Agent，获取完整响应
        
        Args:
            prompt: 用户输入的提示词
            history: 历史消息列表
            
        Returns:
            完整的响应结果
        """
        # 准备初始消息
        initial_messages = history or []
        initial_messages.append(HumanMessage(content=prompt))
        
        # 调用 Agent 图
        result = self.agent.invoke({
            "messages": initial_messages,
            "llm_calls": 0
        })
        
        # 返回最后一条消息的内容
        return result["messages"][-1].content
