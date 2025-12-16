from typing import TypedDict
from langgraph.types import interrupt, Command,RetryPolicy
from langchain.messages import AnyMessage,HumanMessage,AIMessage,ToolMessage
from typing_extensions import Annotated
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import threading
import time
import random
'''
    一些使用方式与建议
'''
class ParallelExecutor:
    ''' 并行执行 '''
    
    class State(TypedDict):
        input: str
        output: str
        messages: Annotated[list[AnyMessage], operator.add] # 合并操作符 每个node返回的message字段会添加到messages字段中
    
    def node1(self, state: State) -> dict:
        time.sleep(3)
        print(f"node1执行,执行时间:{time.time()}\n")
        return {
            "messages": [AIMessage(content=f"node1已收到用户输入:{state['input']}")]
        }
    
    def node2(self, state: State) -> dict:
        # 模拟耗时操作
        time.sleep(3)
        print(f"node2执行,执行时间:{time.time()}\n")
        return {
            "messages": [AIMessage(content=f"node2已收到用户输入:{state['input']}")]
        }
    
    def node3(self, state: State) -> dict:
        time.sleep(3)
        print(f"node3执行,执行时间:{time.time()}\n")
        return {
            "messages": [AIMessage(content=f"node3已收到用户输入:{state['input']}")]
        }
    
    def end_node(self, state: State) -> dict:
        print(f"end_node执行,执行时间:{time.time()}\n")
        return {
            "messages": [AIMessage(content=f"end_node已收到用户输入:{state['input']}")],
            "output": '执行完成!'
        }

    def __init__(self):
        # 获取当前线程id
        self.thread_id = threading.get_ident()
        graph = StateGraph(self.State)
        graph.add_node("node1", self.node1)
        graph.add_node("node2", self.node2)
        graph.add_node("node3", self.node3)
        graph.add_node("end_node", self.end_node)

        graph.add_edge(START,"node1")
        graph.add_edge(START,"node2")
        graph.add_edge(START,"node3")
        graph.add_edge("node1","end_node")
        graph.add_edge("node2","end_node")
        graph.add_edge("node3","end_node")
        graph.add_edge("end_node",END)

        self.graph = graph.compile(checkpointer=MemorySaver())

    def run(self, input: str):
        ''' 运行并行执行 '''
        from IPython.display import Image, display
        display(Image(self.graph.get_graph(xray=True).draw_mermaid_png()))
        result = self.graph.invoke({"input":input}, {"configurable": {"thread_id": self.thread_id}})
        for m in result["messages"]:
            m.pretty_print()

class FeedbackExecutor:
    ''' 
        反馈执行/循环执行
        图中可以有检测节点,不符合继续执行条件的可以跳回到已执行节点重新执行,直到满足条件为止
    '''
    class State(TypedDict):
        input: str
        output: str
        messages: Annotated[list[AnyMessage], operator.add]

        search_param: str # 查询参数
        doc: str  # 文档内容
        cur_index: int = 0 # 当前查询索引
        target_index: int = 0 # 目标文档所在索引

    def analysis_node(self, state: State) -> dict:
        ''' 分析节点 '''
        return {
            "search_param": state["input"],
            "target_index": random.randint(0, 9)
        }

    def search_node(self, state: State) -> dict:
        ''' 搜索节点 '''
        doc = ''
        output = ''
        if(state["cur_index"] == state["target_index"]):
            doc = "成功找到指定文档"
            output = "查询成功"
        return {
            "doc": doc,
            "cur_index": state["cur_index"]+1,
            "output": output
        }

    def judge_node(self, state: State) -> dict:
        ''' 判断节点 '''
        if(state["doc"] == ""):
            return "next_page"
        else:
            return "end"
    
    def __init__(self) -> None:
        self.thread_id = threading.get_ident()
        graph = StateGraph(self.State)
        graph.add_node("analysis_node", self.analysis_node)
        graph.add_node("search_node", self.search_node)
    
        graph.add_edge(START,"analysis_node")
        graph.add_edge("analysis_node","search_node")
        graph.add_conditional_edges("search_node",
        self.judge_node,# 节点分支条件函数
        { # 根据分支函数返回值 路由到不同的节点
            "next_page": "search_node",
            "end": END
        })
        self.graph = graph.compile(checkpointer=MemorySaver())
    
    def run(self, input: str):
        ''' 运行反馈执行 '''
        from IPython.display import Image, display
        display(Image(self.graph.get_graph(xray=True).draw_mermaid_png()))
        result = self.graph.invoke({"input":input,"cur_index": 0}, {"configurable": {"thread_id": self.thread_id}})
        for m in result["messages"]:
            m.pretty_print()
        print(f"最终输出: {result['output']}")
        print(f"最终文档: {result['doc']}")
        print(f"最终查询索引: {result['cur_index']}")

if __name__ == "__main__":
    # executor = ParallelExecutor()
    # executor.run("你好")

    feedback_executor = FeedbackExecutor()
    feedback_executor.run("你好")