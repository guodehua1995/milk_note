from typing import TypedDict
from langgraph.types import interrupt, Command,RetryPolicy
from langchain.messages import AnyMessage,HumanMessage,AIMessage,ToolMessage
from typing_extensions import Annotated
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

'''
    langgraph的错误处理
    see https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph#llm-recoverable
    
    主要内容
    不同类型错误需匹配差异化处理方案，核心要点如下：
        瞬时错误（网络问题、速率限制）：由系统自动修复，采用 “重试机制”，适用于重试后通常可解决的临时故障。
        LLM 可恢复错误（工具故障、解析问题）：由 LLM 自行处理，通过 “将错误存入状态并循环重试” 解决，适用于 LLM 能识别错误并调整策略的场景。
        用户可修复错误（信息缺失、指令模糊）：需用户介入，通过 “调用 interrupt () 暂停” 处理，适用于必须用户补充信息才能推进的情况。
        意外错误：由开发者处理，采用 “让错误直接上报” 的方式，适用于需调试的未知问题。
'''


class ErrorResolveState(TypedDict):
    '''
        错误处理全局状态
    ''' 
    messages: Annotated[list[AnyMessage], operator.add]
    error_type: str

    retry_count: int = 0

def start_node(state: ErrorResolveState) -> Command:
    '''
        开始节点
    '''
    error_type = state["error_type"] 
    if(error_type == "unknown"):
        raise Exception("未知错误类型")

    return Command(
        update={},
        goto= error_type
    )

def net_error(state: ErrorResolveState) -> Command:
    '''
        网络错误节点
    '''
    if(state["retry_count"] < 2):
        state["retry_count"] += 1
        print(f"网络错误重试次数{state['retry_count']}")
        raise Exception("网络错误重试次数超过3次")

    # 模拟ai调用
    state["messages"].append(
        AIMessage(content="网络通畅,AI已成功回答您的问题！")
    )
    return Command(
        update={
            "retry_count": 0
        },
        goto= "end_node"
    )

def llm_error(state: ErrorResolveState) -> Command:
    '''
        LLM错误节点
    '''
    print("进入LLM错误节点...")

    if(state["retry_count"] == 0):
        state["messages"].append(
            ToolMessage(tool_call_id="123",content="工具调用错误,错误内容是:输入的json无法正常解析,请检查json格式后重试")
        )
        
        return Command(
            update={
                "retry_count": state["retry_count"]+1
            },
            goto= "start" # 回到开始节点重新处理
        )

    state["messages"].append(ToolMessage(tool_call_id="456",content="工具调用成功!"))

    # 模拟ai调用
    state["messages"].append(
        AIMessage(content="工具调用成功: 已成功回答您的问题！")
    )
    return Command(
        update={
            "retry_count": 0
        },
        goto= "end_node"
    )

def param_error(state: ErrorResolveState) -> Command:
    '''
        参数错误节点
    '''
    user_input = interrupt({
        "message": "工具调用错误,错误内容是:缺少参数【用户名】"
    })

    user_name = user_input["user_name"]
    state["messages"].append(
        ToolMessage(tool_call_id="789",content=f"工具调用成功: 用户名是【{user_name}】")
    )
    return Command(
        update={
            "retry_count": 0
        },
        goto= "end_node"
    )

def end_node(state: ErrorResolveState) -> Command:
    '''
        结束节点
    '''
    return Command(
        update={},
        goto= END
    )

graph = StateGraph(ErrorResolveState)
# 添加节点
graph.add_node('start',start_node)
graph.add_node('net_error',net_error,retry_policy = RetryPolicy(max_attempts=3, initial_interval=1.0))# 设置重试次数
graph.add_node('llm_error',llm_error)
graph.add_node('param_error',param_error)
graph.add_node('end_node',end_node)

# 建立关系 因为每个节点里已经写好了goto 所以这里只需要添加一个Start节点
graph.add_edge(START,'start')

# 添加checkpointer,确保中断后可以恢复
agent = graph.compile(checkpointer=MemorySaver())
# 展示工作流
from IPython.display import Image, display
display(Image(agent.get_graph(xray=True).draw_mermaid_png()))

# 执行工作流
from langchain.messages import HumanMessage
messages = [HumanMessage(content="你好")]
thread_config = {"configurable": {"thread_id": "customer_123"}}
first_result = agent.invoke({"messages": messages,"error_type": "param_error","retry_count": 0},thread_config)
messages = first_result["messages"]
if first_result.get('__interrupt__') is not None:
    print(first_result['__interrupt__'])
    user_input = input("请输入用户名: ")
    messages.append(HumanMessage(content=user_input))
    continue_command = Command(
        resume= {
            "user_name": user_input
        }
    )
    second_result = agent.invoke(continue_command,thread_config)
    messages = second_result["messages"]

for m in messages:
    m.pretty_print()