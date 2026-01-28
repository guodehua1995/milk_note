'''
    langgraph的状态管理
    see https://docs.langchain.com/oss/python/langgraph/persistence

    前几个课程中创建的graph都传入了MemorySaver()
    目的是将graph的执行过程保存到内存中,用来进行断点续传和实现图内的变量共享。
    本次主要内容是基于内存的状态管理,包括:
        使用thread_id获取graph的状态和所有状态。
        使用checkpoint_id来从指定节点重新执行graph。

'''
from langchain.messages import AIMessage
from langgraph.graph import StateGraph, START, END,MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from typing import Annotated
from typing_extensions import TypedDict
from operator import add
import threading

class NormalGraph:
    '''
       一个最普通的graph,使用内存管理状态
    '''
    class State(TypedDict):
        foo: str
        bar: Annotated[list[str], add]

    def node_a(self, state: State):
        return {"foo": "a", "bar": ["a"]}

    def node_b(self, state: State):
        return {"foo": "b", "bar": ["b"]}

    def judge(self, state: State):
        '''
            判断是否继续执行graph
        ''' 
        if len(state["bar"]) < 4:
            return "continue"
        else:
            return "end"
       

    def __init__(self):
        workflow = StateGraph(self.State)
        workflow.add_node(self.node_a)
        workflow.add_node(self.node_b)
        workflow.add_edge(START, "node_a")
        workflow.add_edge("node_a", "node_b")
        workflow.add_conditional_edges("node_b", self.judge,{
            "continue": "node_a",
            "end": END
        })
        checkpointer = InMemorySaver()
        self.graph = workflow.compile(checkpointer=checkpointer)
        self.thread_id = threading.get_ident()

    def invoke(self, input: str):
        '''
            执行graph,并返回结果,代表graph的一次执行
        '''
        return self.graph.invoke({"foo": "", "bar":[]}, {"configurable": {"thread_id": self.thread_id}})

    def get_last_state(self):
        '''
            获取graph的最后一个状态
        '''
        return self.graph.get_state({"configurable": {"thread_id": self.thread_id}})
    
    def get_all_states(self):
        '''
            获取graph的所有状态
        '''
        return self.graph.get_state_history({"configurable": {"thread_id": self.thread_id}})
    
    def continue_invoke(self, checkpoint_id: str):
        '''
            继续执行graph,并返回结果,代表graph的一次执行
        '''
        return self.graph.invoke(None, {"configurable": {"thread_id": self.thread_id, "checkpoint_id": checkpoint_id}})


from langgraph.store.memory import InMemoryStore

class ShareStateGraph:
    '''
        一个可以在不同线程之间共享状态的graph
        以同一用户在不同设备间共享对话记录为例
    '''

    def llm_call(self,state:MessagesState,config:RunnableConfig,*,store:InMemoryStore):
        user_input = state["messages"][-1]['content']
        return {
            "messages" : AIMessage(content=f"模型已经收到了来自设备{self.client_id}的输入:{user_input}")
        }



    def __init__(self,user_id:str,client_id:str,memory_store:InMemoryStore):
        self.memory_store = memory_store
        self.thread_id = threading.get_ident()
        self.user_id = user_id
        self.client_id = client_id

        graph = StateGraph(MessagesState)
        graph.add_node(self.llm_call)
        graph.add_edge(START, "llm_call")
        graph.add_edge("llm_call", END)
        checkpointer = InMemorySaver()

        self.graph = graph.compile(checkpointer=checkpointer)



if __name__ == "__main__":
    graph = NormalGraph()
    graph.invoke("input")
    print("graph执行后的最终状态:")
    print(graph.get_last_state())
    print("graph第一次执行的所有状态:")
    all_snapshot = list(graph.get_all_states())  # 转换为列表，支持下标访问
    for s in all_snapshot :
        print(s)
    print("graph第一次执行的snapshot长度:"+str(len(all_snapshot)))
    replay_snapshot = all_snapshot[-2]  # 现在可以使用下标访问了
    print("graph第二次执行的起始状态:")
    print(replay_snapshot)
    replay_checkpoint_id = replay_snapshot.config['configurable']["checkpoint_id"]  # StateSnapshot对象使用点号访问属性
    print("graph第二次执行的checkpoint_id:")
    graph.continue_invoke(replay_checkpoint_id)
    all_snapshot = list(graph.get_all_states()) 
    print("graph第二次执行后snapshot长度:"+str(len(all_snapshot)))