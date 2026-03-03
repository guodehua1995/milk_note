from typing import TypedDict, Literal

from langchain.messages import AnyMessage, SystemMessage, HumanMessage
from api.core import settings,get_logger,get_db
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from api.services.tools import web_search
from api.models import Task, TaskExecution
from typing import List
from datetime import datetime

logger = get_logger(__name__)
class SearchTask(TypedDict):
    '''
        搜索任务
    '''
    search_type: Literal["child_search", "doc_search", "web_search"]
    search_content: str | None
    search_result: str | None = None

class SearchPlan(TypedDict):
    '''
        搜索计划
    '''
    search_tasks: list[SearchTask] | None
    is_need_search: bool = False
    count: int = 0

class TaskChatState(TypedDict):
    '''
    任务聊天状态
    '''
    # 当前查询的任务
    task: str  = None
    child_tasks: str | None = None

    messages: list[AnyMessage] | None = None

    search_plan: SearchPlan | None = None

class TaskChatAgent:
    __THINK_PROMPT="""
    # 你的身份
    你是一个资料查询助手,用户为自己设立了一个目标。现在用户针对这个目标提出了一些问题。请你结合用户输入和目标内容,判断是否需要查询额外的资料,如果需要的话,则按指定结构输出查询内容。

    # 查询方式
    确定查询方式后,请生成与查询方式匹配的查询内容,查询内容需要简要且精确,准确的匹配用户需要与查询方式。
    允许多次调用同一个查询方式,以补充信息回答用户问题。
    - doc_search: 知识库搜索,查询用户收集的与目标相关的文档,后续将提供知识库说明。请你结合知识库说明判断是否需要使用知识库搜索。请注意: 当用户提到[查询文档/根据文档xxx/查询知识库]时,必须使用知识库搜索。
    - web_search: 互联网搜索,作为补充搜索方式。当回答用户输入涉及到最新/政策/某项超出你知识范围的专业内容时,请使用互联网搜索。请注意： 当用户提到[使用互联网/结合互联网]等内容时,必须使用互联网搜索。
    搜索关键词:  
        - doc_search: 如果用户提到了具体文档名,则关键字为此文档名。否则需要根据用户问题提取出精确的一个或多个关键词作为搜索条件。
        - web_search: 如果用户提到了具体互联网内容,则关键字为此内容内容。否则需要根据用户问题提取出精确的一个或多个关键词作为搜索条件。

    # 输出结构
    ```json
    {{
        "search_tasks": [
            {{
                "search_type": "child_search", "search_content": "子目标id"
            }}
            {{
                "search_type": "doc_search", "search_content": "用户目标"
            }}
        ],
        "count": 0,
        "is_need_search": true
    }}
    ```
    # 特殊情况
    当依据现有知识即可回答用户问题时,请返回空数组

    # 当前任务信息
    {task}

    # 当前任务子任务信息
    {child_tasks}

    # 知识库描述
    {knowledge_description}

    
    """

    __ANSWER_PROMPT="""
    # 你的身份
    你是一个任务咨询助手,用户正在针对他自己设置的某项任务进行咨询,请你根据任务信息与前面已完成的相关搜索资料,正确回答用户问题。

    # 任务信息
    {task}
    
    # 当前任务子任务信息
    {child_tasks}

    # 搜索结果
    {search_results}
    """

    '''
    任务聊天智能体
    '''
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key= settings.MILK_NOTE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen3-max",
            temperature=0.7
        )
        self.agent = self.__create_agent()
        self.db = next(get_db())

    def __think_node(self, state: TaskChatState)->Command:
        '''
        规划节点
        '''
        logger.debug(f"用户提问已到达规划节点:{state['messages'][-1].content}")

        task_info = f"### 用户咨询任务 \n 标题: {state['task']}"

        knowledge_description = "暂无关联知识库"
        child_tasks_info = state["child_tasks"]
        
        prompt = self.__THINK_PROMPT.format(
            task=task_info,
            knowledge_description=knowledge_description,
            child_tasks=child_tasks_info
        )
        messages = [SystemMessage(content=prompt)]
        messages.extend(state["messages"])
        search_plan = self.llm.with_structured_output(
            SearchPlan
        ).invoke(messages)
        logger.debug(f"规划节点输出: {search_plan}")
        if search_plan["is_need_search"]:
            return Command(goto="search",update={
                "search_plan": search_plan
            })
        else:
            return Command(goto="answer",update={
                "search_plan": search_plan
            })

    def __search_node(self, state: TaskChatState)->Command:
        '''
        搜索节点
        根据搜索计划,执行搜索任务,并更新搜索结果
        '''
        search_plan = state["search_plan"]
        search_results = []
        for search_task in search_plan["search_tasks"]:
            try:
                search_content = search_task["search_content"]
                search_result = ""
                if search_task["search_type"] == "web_search":
                    search_result = web_search(search_content)
                elif search_task["search_type"] == "doc_search":
                    search_result = "暂无知识库"
                else:
                    search_result = "不支持的查询方式"
                search_task["search_result"] = search_result
                search_results.append(search_task)
            except:
                continue
            
        search_plan["search_tasks"] = search_results
        state["search_plan"] = search_plan
        return Command(goto="answer")

    
    def __answer_node(self, state: TaskChatState)->Command:
        '''
        回答节点
        根据搜索计划,生成回答
        '''
        logger.debug(f"用户提问已到达回答节点:{state['messages'][-1].content}")
        
        search_plan = state["search_plan"]
        if search_plan and search_plan["search_tasks"]:
            search_results = search_plan["search_tasks"]
        else:
            search_results = []
    
        system_message = [SystemMessage(content=self.__ANSWER_PROMPT.format(
            task=state["task"],
            child_tasks=state["child_tasks"],
            search_results=search_results
        ))]
        messages = system_message + state["messages"]
        self.llm.invoke(messages,{
            "tags": ["stream_to_user"]
        })
        return Command(goto=END)


    def __create_agent(self):
        '''
        创建智能体
        '''
        graph = StateGraph(TaskChatState)
        graph.add_node("think", self.__think_node)
        graph.add_node("search", self.__search_node)
        graph.add_node("answer", self.__answer_node)
        graph.add_edge(START, "think")
        graph.add_edge("answer", END)
        return graph.compile(checkpointer=InMemorySaver())

    def ask_stream(self, user_id: int, task_info: str, child_task_info: str, historys: list[dict], user_message: str):
        '''
        任务咨询
        '''
        state = {
            "task": task_info,
            "child_tasks": child_task_info,
            "messages": historys+[HumanMessage(content=user_message)]
        }
        return self.agent.stream(state,{"configurable": {"thread_id": str(user_id)}},stream_mode="messages")
