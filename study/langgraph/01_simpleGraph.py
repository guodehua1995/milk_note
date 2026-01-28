from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage,ToolMessage
import os
from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
from typing import Literal
from langgraph.graph import StateGraph, START, END
import operator

api_key = os.environ.get("MILK_NOTE_API_KEY")
model = ChatOpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    temperature=0.7
)

# Define tools
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


# Augment the LLM with tools
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)



class MessagesState(TypedDict):
    '''
    消息状态
    messages: 消息列表 AnyMessage 任意消息类型 operator.add 添加操作
    llm_calls: 调用次数
    '''
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

def llm_call(state: dict):
    """
    LLM调用
    由模型判断是否使用工具
    """

    return {
        "messages": [ # 调用模型并返回消息列表
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1 # 增加模型调用次数
    }

def tool_node(state: dict):
    """执行工具调用"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]] # 根据工具名称获取工具
        observation = tool.invoke(tool_call["args"]) # 调用工具并获取结果
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"])) # 添加工具消息
    return {"messages": result}

def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """
    根据大语言模型是否进行了工具调用，来决定我们是继续循环还是停止循环。
    """

    messages = state["messages"]
    last_message = messages[-1]

    # 如果大语言模型（LLM）进行工具调用，那么就执行一个操作
    if last_message.tool_calls:
        return "tool_node"

    # 否则,回复用户
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
agent_builder.add_edge("tool_node", "llm_call") # 工具节点调用后，携带工具调用结果继续调用LLM

# 完成工作流
agent = agent_builder.compile()

# 展示工作流
from IPython.display import Image, display
display(Image(agent.get_graph(xray=True).draw_mermaid_png()))

# 执行工作流
from langchain.messages import HumanMessage
messages = [HumanMessage(content="multiply 3 and 4.")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()

# 一个最简单的工作流就搭建好了