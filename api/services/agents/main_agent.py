from typing import TypedDict
from venv import logger
from api.models import ChatHistory
from langchain.messages import AnyMessage
from typing_extensions import Annotated
from api.core import settings, logger
from langchain_openai import ChatOpenAI
import os
from langgraph.graph import StateGraph, START, END
import operator
from langgraph.checkpoint.memory import InMemorySaver

class MainState(TypedDict):
    '''
    主智能体状态
    messages: 消息列表 AnyMessage 任意消息类型 operator.add 添加操作
    llm_calls: 调用次数
    '''
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int | None = 0

class MainAgent:
    '''
    主智能体
        负责处理用户与助手的交互
    '''
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.llm = ChatOpenAI(
            api_key= settings.MILK_NOTE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            temperature=0.7
        )
        self.agent = self.__create_agent()

    def __llm_call(self, state: MainState) -> MainState:
        '''
        LLM调用节点
        '''
        messages = state["messages"]
        response = self.llm.invoke(messages)
        state["messages"].append(response)
        if state["llm_calls"] is None:
            state["llm_calls"] = 0
        state["llm_calls"] += 1
        return state

    def __create_agent(self) -> StateGraph:
        '''
        创建主智能体工作流
        '''
        graph = StateGraph(MainState)
        graph.add_node("llm_call", self.__llm_call)
        graph.add_edge(START, "llm_call")
        graph.add_edge("llm_call", END) # 工具节点调用后，携带工具调用结果继续调用LLM
        return graph.compile(checkpointer=InMemorySaver())

    def agent_stream(self, input: str):
        '''
        执行主智能体工作流
        '''
        return self.agent.stream({"messages": [{"role": "user", "content": input}], "llm_calls": 0}, {"configurable": {"thread_id": self.user_id}},stream_mode="messages")