from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool,tool
from langchain.agents import create_agent

import os
import logging

@tool
def get_weather(query: str) -> str:
    """查询当前天气"""
    return f"{query}的天气是阴天"

class Agent:
    def __init__(self,tools:list):
        api_key = os.environ.get("MILK_NOTE_API_KEY")
        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            temperature=0.7
        )
        self.tools = tools
        self.agent = create_agent(model=llm, tools=tools,system_prompt="You are a helpful assistant")

    def ask(self,query:str):
        return self.agent.invoke( {"messages": [{"role": "user", "content": query}]})


agent = Agent([get_weather])

response = agent.ask("请问健身期间,应该如何注意饮食呢")
print(response)
