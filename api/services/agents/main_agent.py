from typing import TypedDict
from venv import logger
from langchain.messages import AnyMessage,SystemMessage,ToolMessage, AIMessage
from typing_extensions import Annotated
from api.core import settings, get_logger,get_db,oss_client
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END
from api.services.tools import TOOL_INFO
import operator
from langgraph.checkpoint.memory import InMemorySaver
import api.services.agents.prompts as prompts
import api.services.agents.models as agent_models
import json
from typing import List
from api.models import ChatHistory
import random
from ..document_service import DocumentService

logger = get_logger(__name__)


class MainState(TypedDict):
    '''
    主智能体状态
    messages: 消息列表 AnyMessage 任意消息类型 operator.add 添加操作
    plans: 计划列表 dict 计划字典 operator.add 添加操作
    llm_calls: 调用次数
    '''
    messages: Annotated[list[AnyMessage], operator.add]
    plan: agent_models.AgentPlan | None = None
    llm_calls: int | None = 0
    user_id: int | None = None
    
    ## 上下文总结
    dialog_summary: str | None = None

    user_input: str | None = None

    tool_logs: str | None = None

class MainAgent:
    '''
    主智能体
        负责处理用户与助手的交互
    '''
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key= settings.MILK_NOTE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-max",
            temperature=0.7
        )
        self.agent = self.__create_agent()

    def __agent_classification_node(self,state: MainState) -> Command:
        '''
        智能体分类节点
        '''
        # 如果历史消息长度超过10 则截取最近10条消息
        if len(state["messages"]) > 10:
            state["messages"] = state["messages"][-10:]

        llm_with_structured_output  = self.llm.with_structured_output(agent_models.AgentClassification)
        current_messages = [SystemMessage(content=prompts.AGENT_CLASSIFICATION_PROMPT)]
        current_messages.extend(state["messages"])
        agent_classification = llm_with_structured_output.invoke(current_messages)
        logger.debug("智能体分类节点分类结果：%s", json.dumps(agent_classification, ensure_ascii=False))
        
        return Command(
            goto = agent_classification["intent"],
            update = {"dialog_summary": agent_classification["dialog_summary"],"llm_calls": state["llm_calls"] + 1}
        )
    
    def __just_talk_node(self, state: MainState) -> Command:
        '''
        只是简单的聊天节点
        '''
        # logger.info("agent分类节点收到消息：%s", state["messages"])
        tool_logs = state.get("tool_logs","")
        if tool_logs == "":
           plan =  state.get("plan",None)
           if plan is not None:
               tool_logs = "\n".join([f"标题:{step['title']};描述:{step['content']};结果:{step['result']};状态:{step['status']}" for step in plan["plans"]])
        current_messages = [SystemMessage(content=prompts.JUST_TALK_PROMPT.format(tool_logs = tool_logs))]
        current_messages.extend(state["messages"])
        response = self.llm.invoke(current_messages,{
            "tags": ["stream_to_user"]
        })
        # logger.info("just talk调用完成")
        return Command(
            update = {"messages": [response],"llm_calls": state["llm_calls"] + 1}
        )
        
    def __plan_node(self, state: MainState) -> Command:
        '''
        计划节点
        '''
        tool_descriptions = {}
        for tool_code in TOOL_INFO.keys():
            tool_descriptions[tool_code] = TOOL_INFO[tool_code].description
        current_messages = [SystemMessage(content = prompts.PLAN_PROMPT.format(tools_info = tool_descriptions))]
        current_messages.extend(state["messages"])

        llm_with_structured_output = self.llm.with_structured_output(agent_models.AgentPlans)
        agent_plan = llm_with_structured_output.invoke(current_messages)
        logger.info("计划节点生成计划：%s", json.dumps(agent_plan, ensure_ascii=False))
        return Command(
            update = {"plan": agent_plan, "llm_calls": state["llm_calls"] + 1},
            goto = "plan_execution"
        )
    
    def __execute_plan_node(self, state: MainState) -> Command:
        '''
        执行计划节点
            执行待执行计划,并根据计划结果,判断是否完成用户需求
            若未完成,则继续执行计划
            若完成,则返回计划结果
        '''
        plan = state["plan"]
        current_step = plan["current_step"]
        # logger.debug(f"执行计划节点,当前计划:{plan}")
        if plan is None:
            logger.error("agent异常,计划为空")
            return Command(
                update = {"messages": [SystemMessage(content="很抱歉,我没能很好的理解您的需求,请重新描述下试试看吧~")]},
                goto = END
            )
         # 重新思考现阶段计划是否需要调整
         # TODO 单独开一个重新思考计划的节点,由计划最后一个节点评估计划是否需要调整
        
        # 若计划执行失败,则返回失败信息
        if  plan["status"] == "failed":
            # 清理所有的工具消息和系统消息
            state["messages"] = [msg for msg in state["messages"] if not isinstance(msg, ToolMessage) and not isinstance(msg, SystemMessage)]
            state["plan"] = None
            logger.error(f"执行计划节点,当前计划:{plan},计划执行失败")
            return Command(
                update = {"messages": [SystemMessage(content="很抱歉,出现了一些意料之外的情况导致没能处理您的问题,请重新描述下试试看吧~")]},
                goto = END
            )

        # 若计划执行成功
        if plan["status"] == "success":
            # 清理所有的工具消息和系统消息
            state["messages"] = [msg for msg in state["messages"] if not isinstance(msg, ToolMessage) and not isinstance(msg, SystemMessage)]
            state["plan"] = None
            return Command(
                goto = END
            )
        
        plans = plan["plans"]
        if len(plans) == current_step + 1:
            # 若计划执行成功,则返回计划结果
            return Command(
                goto = "just_talk"
        )
        current_plan =  plans[current_step]
        logger.info(f"当前计划:{current_plan}")
        #TODO 当前计划执行失败,调用重新思考计划节点,判断是否需要重新执行。

        

        # logger.debug(f"当前计划:{current_plan}")
        return Command(
            update = {"plan": plan, "llm_calls": state["llm_calls"] + 1},
            goto = current_plan["intent"] 
        )

    def __plan_llm_call_node(self, state: MainState) -> Command:
        '''
        计划LLM调用节点
        '''
        # logger.debug(f"计划LLM调用节点,当前消息:{state['messages']}")
        plan = state["plan"]
        plans = plan["plans"]
        current_step = plan["current_step"]
        current_plan =  plans[current_step]

        try:
            current_prompt = prompts.PLAN_LLM_PROMPT.format(
                plans = plans,
                current_plan = current_plan,
            )
            logger.error(f"计划LLM调用节点,当前模型输入:{current_prompt}")
            current_plan = self.llm.with_structured_output(agent_models.AgentPlan).invoke(current_prompt)
            # logger.info(f"计划LLM调用节点,当前计划:{current_plan['title']},计划执行成功,返回结果:{response}")
            plans[current_step] = current_plan
            plan["current_step"] += 1
        except Exception as e:
            logger.error(f"计划LLM调用节点,当前计划:{current_plan['title']},计划执行失败,错误信息:{e}")
            current_plan["status"] = "failed"

        return Command(
            update = {"plan": plan, "llm_calls": state["llm_calls"] + 1},
            goto = "plan_execution"
        )

    def __plan_tools_use_node(self, state: MainState) -> Command:
        '''
        计划工具调用节点
        '''
        # logger.debug(f"计划工具调用节点,当前消息:{state['messages']}")
        plan = state["plan"]
        plans = plan["plans"]
        current_plan =  plans[plan["current_step"]]

        tool_messages = []
        try:
            # 1.选择工具
            tool_descriptions = {}
            for tool_code in TOOL_INFO.keys():
                tool_descriptions[tool_code] = TOOL_INFO[tool_code].description
            # logger.debug(f"工具调用节点,当前工具描述:{tool_descriptions}")
            # TODO 缺少计划执行上下文
            current_prompt = prompts.TOOL_CHOICE_PROMPT.format(tools_info = tool_descriptions, dialog_summary = f"用户需求:{current_plan['title']},需求描述:{current_plan['content']}")
            # logger.debug(f"工具调用节点,当前模型输入:{current_prompt}")
            tool_choice: agent_models.ToolChoice =  self.llm.with_structured_output(agent_models.ToolChoice).invoke(current_prompt)

            # 执行工具调用
            tools = [TOOL_INFO[tool_code] for tool_code in tool_choice["tools"] if tool_code in TOOL_INFO]
            tool_messages = []
            tool_result_history = ""
            for tool in tools:
                if tool.empty_param:
                    observation = tool.func.invoke("")
                    tool_messages.append(ToolMessage(content=observation, tool_call_id="empty_param",tool_name = tool.tool_name)) # 添加工具消息
                else:
                    system_prompt = prompts.TOOL_USE_PROMPT.format(chat_history = state["messages"], tool_result_history = tool_result_history, current_user_query =tool_choice["work_flow"] )
                    # logger.debug(f"工具调用节点,当前模型输入:{system_prompt}")
                    tool_use = self.llm.bind_tools([tool.func]).invoke(system_prompt)
                    for tool_call in tool_use.tool_calls:
                    #3. 执行工具,收集结果
                        observation = tool.func.invoke(tool_call["args"]) # 调用工具并获取结果
                        # logger.debug(f"工具调用节点,当前工具调用:{tool_call}成功,参数为:{tool_call['args']}")
                        tool_messages.append(ToolMessage(content=observation, tool_call_id=tool_call["id"],tool_name = tool.tool_name)) # 添加工具消息
                #4. 跳转到下一个节点进行总结
                tool_result_history = "\n".join([f"工具:{tool_msg.tool_name},结果:{tool_msg.content}" for tool_msg in tool_messages if isinstance(tool_msg, ToolMessage)])
                
            
            current_plan["result"] = tool_result_history
            current_plan["status"] = "success"
            plan["current_step"] += 1
        except Exception as e:
            logger.error(f"计划工具调用节点,当前计划:{current_plan},当前错误:{e}")
            current_plan["result"] = "此任务执行失败"
            current_plan["status"] = "failed"
        
        return Command(
            update = {"plan": plan, "llm_calls": state["llm_calls"] + 1},
            goto = "plan_execution"
        )

    def __plan_decomposition_node(self, state: MainState) -> Command:
        '''
        计划分解节点
        '''
        logger.debug(f"计划分解节点,当前消息:{state['messages']}")
        plan = state["plan"]
        plans = plan["plans"]
        current_plan =  plans[plan["current_step"]]

        plan["status"] = "success"

        logger.info(f"计划分解节点,当前计划:{current_plan}")

        return Command(
            update = {"messages": state["messages"]+ [AIMessage(content=f"计划分解节点已经收到任务:{current_plan['content']}咯,之后会真的分解计划的,现在只是调试阶段。")],"plan": plan, "llm_calls": state["llm_calls"] + 1},
            goto = "plan_execution"
        )

    def __tools_use_node(self, state: MainState) -> Command:
        '''
        工具调用节点
        '''
        #1. 将所有的工具描述提供给模型,由模型选择可能用到的工具 
        tool_descriptions = {}
        for tool_code in TOOL_INFO.keys():
            tool_descriptions[tool_code] = TOOL_INFO[tool_code].description
        # logger.debug(f"工具调用节点,当前工具描述:{tool_descriptions}")
        current_prompt = prompts.TOOL_CHOICE_PROMPT.format(tools_info = tool_descriptions, dialog_summary = state["dialog_summary"])
        # logger.debug(f"工具调用节点,当前模型输入:{current_prompt}")
        tool_choice =  self.llm.with_structured_output(agent_models.ToolChoice).invoke(current_prompt)

        # 执行工具调用
        tools = [TOOL_INFO[tool_code] for tool_code in tool_choice["tools"] if tool_code in TOOL_INFO]

        tool_messages = []
        tool_result_history = ""
        for tool in tools:
            if tool.empty_param:
                observation = tool.func.invoke("")
                tool_messages.append(ToolMessage(content=observation, tool_call_id="empty_param",tool_name = tool.tool_name)) # 添加工具消息
            else:
                system_prompt = prompts.TOOL_USE_PROMPT.format(chat_history = state["messages"], tool_result_history = tool_result_history, current_user_query =tool_choice["work_flow"] )
                # logger.debug(f"工具调用节点,当前模型输入:{system_prompt}")
                tool_use = self.llm.bind_tools([tool.func]).invoke(system_prompt)
                for tool_call in tool_use.tool_calls:
                #3. 执行工具,收集结果
                    observation = tool.func.invoke(tool_call["args"]) # 调用工具并获取结果
                    # logger.debug(f"工具调用节点,当前工具调用:{tool_call}成功,参数为:{tool_call['args']}")
                    tool_messages.append(ToolMessage(content=observation, tool_call_id=tool_call["id"],tool_name = tool.tool_name)) # 添加工具消息
            #4. 跳转到下一个节点进行总结
            tool_result_history = "\n".join([f"工具:{tool_msg.tool_name},结果:{tool_msg.content}" for tool_msg in tool_messages if isinstance(tool_msg, ToolMessage)])
            
            logger.debug(f"工具调用节点,当前工具调用结果:{tool_result_history}")
        return Command(
            update = {"tool_logs": tool_result_history, "llm_calls": state["llm_calls"] + 1},
            goto = "just_talk"
        )

    def __search_node(self, state: MainState) -> Command:
        """
        搜索节点
        判断使用互联网/Rag/混合搜索满足用户需求
        """

        # 1. 根据用户消息判断搜索类型和搜索关键词/内容
        current_prompts = [SystemMessage(content=prompts.SEARCH_ANALYSIS_PROMPT)]
        current_prompts.extend(state["messages"])
        r = self.llm.with_structured_output(agent_models.SearchType).invoke(current_prompts)
        search_type = r["search_type"]
        search_content = r["search_content"]
        if search_content == "":
            logger.error("搜索节点,搜索内容为空")
            return Command(
                update = {"messages": [AIMessage(content="很抱歉,我没能很好的理解您的需求,请重新描述下试试看吧~")]},
                goto = END
            )
        # 2. 根据搜索类型进行搜索
        references = '' 
        user_id = state["user_id"]
        if search_type == "rag_only":
            # RAG知识库搜索
            document_service = DocumentService(next(get_db()))
            chunks = document_service.search_similar_chunks(search_content, user_id, limit=5, threshold=0.1)
            logger.debug(f"搜索节点,当前搜索结果:{chunks}")
            # 查询chunk所属的文档url
            for chunk in chunks:
                document = document_service.get_document_by_id(chunk["document_id"], user_id)
                references += f"来源:知识库\n 文档内容:{chunk["content"]}\n 引用文档名称:{document.file_name}\n 引用文档url:{oss_client.path_for_download(document.file_key)}\n"
        elif search_type == "web_search_only":
            # Web搜索
            web_search_results = TOOL_INFO['web_search_tool'].func.invoke({"query": search_content, "count": 5})
            references += f"来源:互联网\n 文档内容:{web_search_results} \n"
        elif search_type == "rag_web_search":
            # 混合搜索
            document_service = DocumentService(next(get_db()))
            chunks = document_service.search_similar_chunks(search_content, user_id, limit=2, threshold=0.1)
            docs = []
            for chunk in chunks:
                docs.append(f"来源:知识库\n 文档内容:{chunk["content"]}\n")
        
            web_search_results = TOOL_INFO['web_search_tool'].func.invoke({"query": search_content, "count": 3})
            docs.append(f"来源:互联网\n 文档内容:{web_search_results}")

            # 打乱顺序
            random.shuffle(docs)
            references = "\n".join(docs)
            
        current_messages = [SystemMessage(content=prompts.SEARCH_REPLY_PROMPT.format(references = references))]
        current_messages.extend(state["messages"])
        response = self.llm.invoke(current_messages,{
                "tags": ["stream_to_user"]
        }) 

        return Command(
            update = {"messages": [response]},
            goto = END
        )

    def __create_agent(self) -> StateGraph:
        '''
        创建主智能体
        '''
        graph = StateGraph(MainState)
        graph.add_node("agent_classification", self.__agent_classification_node)
        graph.add_node("plan_node", self.__plan_node)
        graph.add_node("plan_llm_call", self.__plan_llm_call_node)
        graph.add_node("plan_tools_use", self.__plan_tools_use_node)
        graph.add_node("plan_decomposition", self.__plan_decomposition_node)
        graph.add_node("just_talk", self.__just_talk_node) 
        graph.add_node("plan_execution", self.__execute_plan_node)
        graph.add_node("tools_use", self.__tools_use_node)
        graph.add_node("search", self.__search_node)

        graph.add_edge(START, "agent_classification")
        graph.add_edge("just_talk", END) 
        graph.add_edge("tools_use", END)
        return graph.compile(checkpointer=InMemorySaver())  

    def agent_stream(self, input: str, history: List[ChatHistory], user_id: int):
        '''
        执行主智能体工作流
        '''
        messages = [{"role": h.type, "content": h.content, "timestamp": h.timestamp.strftime("%Y-%m-%d %H:%M:%S")} for h in history] + [{"role": "user", "content": input}]
        return self.agent.stream({"messages": messages, "llm_calls": 0, "user_id": user_id}, {"configurable": {"thread_id": str(user_id)}},stream_mode="messages")
