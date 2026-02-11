from typing import TypedDict, Literal
from api.core import settings,get_logger
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from api.services.agents.models import SearchType
from api.services.tools import web_search
from api.models import Task, TaskExecution
from typing import List
from datetime import datetime

logger = get_logger(__name__)

think_prompt = """
# 你的身份
你是一个计划辅助智能体,用户将告知你他的目标和执行情况,请你根据用户目标与当前执行情况与用户自身已经搜索过的一些信息。
请你根据这些信息判断是否需要进行搜索来补充额外信息。

# 输入说明
- 用户目标: 用户像达成的最终目标。
- 用户过往执行情况: 根据用户计划执行情况所总结的一段文字,用来说明用户整体的执行情况。
- 用户近期执行情况: 用户最近几次执行情况的日志,用来说明用户最近的执行情况。
- 用户搜索结果: 用户已经搜索过的一些结果,用来说明用户已经搜索过的内容。
- 知识库描述: 知识库的描述,你可以根据知识库说明判断是否需要进行知识库搜索。

# 工作流程
1. 你需要通读用户目标与执行情况和用户的搜索结果,并进行理解。
2. 你需要根据以上信息,判断用户是否在按计划实现自己的目标。
3. 无论用户是否在按计划实现目标,你需要根据以上信息,判断依靠你自身知识是否能满足用户目标。
4. 如果不能,你需要生成一个搜索计划,后续用户搜索后会将搜索结果输入给你,以便你再次执行上述任务。

# 用户目标
## {task_title}
{task_description}

# 用户过往执行情况
{task_context}

# 用户近期执行情况
{task_executionutions}

# 用户搜索结果
{search_results}

# 知识库描述
{knowledge_description}

# 输出结构
```json
{{
    "search_params": [
        {{
            "search_type": "rag_only",
            "search_content": "用户目标"
        }}
    ],
    "count": 0,
    "is_need_search": true
}}
```
"""

summary_prompt = """
# 你的身份
你是一个计划辅助智能体,你需要结合用户提供的资料,根据用户的目标与执行情况对用户过往执行情况进行规划。并生成未来执行的建议。以markdown格式输出。
请注意: 只输入markdown格式的过往执行情况与未来执行建议,禁止输出任何无关文字。

# 输入说明
- 用户目标: 用户像达成的最终目标。
- 用户过往执行情况: 根据用户计划执行情况所总结的一段文字,用来说明用户整体的执行情况。
- 用户近期执行情况: 用户最近几次执行情况的日志,用来说明用户最近的执行情况。
- 用户搜索结果: 用户已经搜索过的一些结果,用来说明用户已经搜索过的内容。

# 用户目标
## {task_title}
{task_description}

# 用户过往执行情况
{task_context}

# 用户近期执行情况
{task_executionutions}

# 用户搜索结果
{search_results}

"""

repeat_task_prompt = """
## 你的身份
你是一个计划智能体,用户将提供给你一个长期目标,你需要将用户的长期目标拆解为多个短期目标,并返回短期目标的列表。
**请注意** 一次最多生成一周(7天)内的短期目标。

## 输入参数说明
- 当前时间: 当前时间,格式为YYYY-MM-DD HH:MM:SS
- 本日为星期几: 本日为星期几,格式为0-6,0表示星期日
- 用户目标: 用户目标的标题
- 用户目标描述: 用户目标的详细描述
- 用户目标上下文: 用户目标的过往执行情况和未来执行方向。
- 目标开始时间: 用户目标的开始时间
- 目标结束时间: 用户目标的结束时间
- 重复周期: never,weekly:1,3,5/monthly:1,15,20 表示不重复,每周重复1,3,5号,每月重复1,15,20号

## 工作流程
1. 根据用户目标标题和用户目标描述完全理解用户目标。
2. 结合用户目标和用户目标上下文,分析出用户目标当前的执行情况与未来执行方向。
3. 结合当前日期和重复周期,计算本周应创建多少短期目标与具体执行日期。
4. 根据每个执行日期与未来执行方向,生成短期目标的内容和标题。

## 输出参数
- executions: 生成的执行短期目标列表。
    - title: 生成的短期目标标题,20个字以内。
    - content: 生成的短期目标详情,执行建议等信息,格式为markdown格式,500个字以内。
    - execution_date: 生成的短期目标执行时间,格式为YYYY-MM-DD

## 输入参数
- 当前时间: {current_time}
- 本日为星期几: {current_day}
- 用户目标: {title} 
- 用户目标描述: {description}
- 用户目标上下文: {task_context}
- 目标开始时间: {start_date}
- 目标结束时间: {end_date}
- 重复周期: {repeat_cycle} 
"""

sub_task_prompt = """
## 你的身份
你是一个计划辅助智能体,现在用户有一个复杂的目标(主任务)需要实现,请你按照规则帮用户将复杂目标拆分为子任务。以更好的逐步实现用户目标。

## 拆分原则
- 子任务数量不超过6个。
- 子任务类型只能为once或repeat。
- 子任务描述为当前任务为了完成主任务需要做的事情,语言简练,不能超过200个字。
- 子任务上下文必须包含子任务的详细描述与后续执行建议,用于AI规划待办事项。 1000字以内。
- 子任务开始时间和结束时间必须在主任务的开始时间和结束时间之间。
- 当子任务为repeat类型时,必须包含重复周期。重复周期格式为: weekly:1,3,5/monthly:1,15,20 代表 每周重复1,3,5号,每月重复1,15,20号。

## 用户主任务
## {task_title}
{task_description}
## 用户主任务上下文
{task_context}
## 用户主任务开始时间
{start_date}
## 用户主任务结束时间
{end_date}

## 子任务字段说明
title: 子任务标题
description: 子任务描述
type: 子任务类型,once/repeat
context: 子任务上下文,用于AI规划待办事项
repeat_cycle: 子任务重复周期,never/weekly:1,3,5/monthly:1,15,20
start_date: 子任务开始时间
end_date: 子任务结束时间

## 输出结构
```json
{{
    "subtasks": [
        {{
            "title": "子任务标题",
            "description": "子任务描述",
            "type": "once",
            "context": "子任务上下文",
            "repeat_cycle": "never",
            "start_date": "子任务开始时间",
            "end_date": "子任务结束时间"
        }}
    ]
}}
```
"""

class SearchPlan(TypedDict):
    '''
        搜索计划

        search_params: 搜索参数列表
        count: 搜索次数
        is_need_search: 是否需要搜索
    '''
    search_params: list[SearchType] | None
    is_need_search: bool = False
    count: int = 0

class State(TypedDict):
    '''
    智能体状态
    '''
    task: Task | None = None
    task_executionutions: List[TaskExecution] | None = None
    search_plan: SearchPlan | None = None
    search_results: List[str] | None = []
    context_result: str | None = None

class RepeatTaskContent(TypedDict):
    '''
        重复任务内容

        title: 重复任务标题
        content: 重复任务内容
        execution_date: 重复任务执行时间
    '''
    title: str
    content: str = ""
    execution_date: str = ""

class RepeatTaskWeeklyPlan(TypedDict):
    '''
        重复任务计划

        executions: 重复任务执行列表
    '''
    executions: list[TaskExecution] | None = None

class SubTask(TypedDict):
    '''
        子任务

        title: 子任务标题
        description: 子任务描述
        type: 子任务类型,once/repeat
        context: 子任务上下文,用于AI规划待办事项
        repeat_cycle: 子任务重复周期,never/weekly:1,3,5/monthly:1,15,20
        start_date: 子任务开始时间
        end_date: 子任务结束时间
    '''
    title: str = ""
    type: Literal["once", "repeat"] = "once"
    description: str = ""
    context: str = ""   
    repeat_cycle: str = ""
    start_date: str = ""
    end_date: str = ""

class ComplexTaskPlan(TypedDict):
    '''
        复杂任务计划

        subtasks: 复杂任务子目标列表
    '''
    subtasks: list[SubTask] | None = None

class TaskPlanAgent:
    '''
    任务计划智能体
    '''
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key= settings.MILK_NOTE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen3-max",
            temperature=0.7
        )
        self.agent = self.__create_agent()

    def complex_task_plan(self,task: Task) -> List[Task]:
        '''
        生成复杂目标的子目标

        Args:
            task: 复杂目标对象

        Returns:
            生成的子目标对象列表
        '''
        prompt = sub_task_prompt.format(
            task_title = task.title,
            task_description = task.description,
            task_context = task.context,
            start_date = task.start_date.strftime("%Y-%m-%d"),
            end_date = task.end_date.strftime("%Y-%m-%d")
        )
        logger.debug(f"复杂任务计划输入: {prompt}")
        # 生成子目标
        subtasks = self.llm.with_structured_output(ComplexTaskPlan).invoke(prompt)
        logger.debug(f"生成子目标: {subtasks}")
        if subtasks["subtasks"] is None:
            return []

        result: List[Task] = []
        for subtask in subtasks["subtasks"]:
            result.append(
                Task(
                    parent_id = task.id,
                    title = subtask["title"],
                    description = subtask["description"],
                    type = subtask["type"],
                    context = subtask["context"],
                    repeat_cycle = subtask["repeat_cycle"],
                    start_date = datetime.strptime(subtask["start_date"], "%Y-%m-%d"),
                    end_date = datetime.strptime(subtask["end_date"], "%Y-%m-%d"),
                    user_id = task.user_id,
                    is_ai_planned = True,
                )
            )
        return result
        

    def repeat_task_plan(self,task: Task) -> List[TaskExecution]:
        '''
        生成一周的重复任务执行列表

        Args:
            task: 任务对象

        Returns:
            重复任务执行列表
        '''
        prompt = repeat_task_prompt.format(
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            current_day = datetime.now().weekday(),
            title = task.title,
            description = task.description,
            task_context = task.context,
            start_date = task.start_date.strftime("%Y-%m-%d"),
            end_date = task.end_date.strftime("%Y-%m-%d"),
            repeat_cycle = task.repeat_cycle
        )

        # 生成当前周的执行单元
        repeat_task_plan =  self.llm.with_structured_output(RepeatTaskWeeklyPlan).invoke(prompt)
        repeat_executions = repeat_task_plan["executions"]
        logger.debug(f"生成重复任务执行列表: {repeat_executions}")
        result:List[TaskExecution] = []
        for execution in repeat_executions:
            result.append(
                TaskExecution(
                task_id = task.id,
                title = execution["title"],
                content = execution["content"],
                execution_date = datetime.strptime(execution["execution_date"], "%Y-%m-%d"),
                user_id = task.user_id,
                )
            )

        return result

    def __think_node(self, state: State)->Command:
        '''
        思考节点
        '''
        task = state["task"]
        not_summaried_executions = [f"执行标题:{e.title} \n 执行内容:{e.content} \n 执行时间:{e.execution_date}\n 执行结果:{e.execution_result}" for e in state["task_executionutions"] if not e.summaried]
        prompt = think_prompt.format(
            task_title = task.title,
            task_description = task.description,
            task_context = task.context,
            task_executionutions = not_summaried_executions,
            search_results = state["search_results"],
            knowledge_description = None # TODO 后续添加知识库
        )

        search_plan = self.llm.with_structured_output(SearchPlan).invoke(prompt)

        goto = "search" if search_plan["is_need_search"] else "summary"
            
        return Command(
            goto = goto,
            update = {"search_plan": search_plan}
        )


    def __search_node(self, state: State) -> Command:
        '''
        搜索节点
        '''
        search_plan = state["search_plan"]
        if search_plan.get("count") >= 3:
            goto = "summary"
        else:
            goto = "think"
            search_plan = state["search_plan"]
            for search_param in search_plan["search_params"]:
                if search_param.get("search_type") == "rag_only":
                    pass
                if search_param.get("search_type") == "web_search_only":
                    search_results = web_search(search_param.get("search_content"),5)
                    state["search_results"].append(search_results)
                if search_param.get("search_type") == "rag_web_search":
                    # TODO 先纯web搜索,后续接入rag
                    search_results = web_search(search_param.get("search_content"),5)
                    state["search_results"].append(search_results)

            search_plan["count"] += 1

        return Command(
            goto = goto,
            update = {"search_plan": search_plan}
        )

    def __summary_node(self, state: State):
        '''
        摘要节点
        '''
        prompt = summary_prompt.format(
            task_title = state["task"].title,
            task_description = state["task"].description,
            task_context = state["task"].context,
            task_executionutions = state["task_executionutions"],
            search_results = state["search_results"]
        )
        return self.llm.invoke(prompt).content

    def __create_agent(self):
        '''
        创建智能体
        1. 智能体执行第一步, 根据上下文与执行情况判断是否需要搜索。
        2. 如果需要搜索,则总结出搜索关键字和搜索列表。可以支持多搜索。
        3. 搜索结束后结合搜索结果再次思考是否需要继续搜索。(最多3次)
        4. 如果不需要则结合搜索结果总结上下文并跳到END节点。
            '''
        graph = StateGraph(State)
        graph.add_node("think", self.__think_node)
        graph.add_node("search", self.__search_node)
        graph.add_node("summary", self.__summary_node)

        graph.add_edge(START, "think")
        graph.add_edge("summary", END) 
        
        return graph.compile(checkpointer=InMemorySaver())  

    def summary_task_context(self, task: Task, executions: List[TaskExecution]) -> str:
        '''
        总结目标上下文
        '''
        state = {
            "task": task,
            "task_executionutions": executions,
            "search_plan": None,
            "search_results": [],
            "context_result": None
        }
        context = self.agent.invoke(state)
        return context