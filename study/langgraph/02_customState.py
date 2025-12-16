from nt import symlink
from typing import TypedDict, Literal
import os
import random
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command, RetryPolicy
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

'''
 自定义全局状态与多节点分支
 假设我们设计一个报告助手,它的需求如下:
 1. 助手可以使用工具进行联网搜索并回答问题
 2. 助手可以根据用户的问题查询文档库
 3. 助手可以发用邮件给指定的人
 4. 发送邮件之前,需要将邮件内容展示给用户,并确认用户是否同意
拆解之后agent执行流程应该如下
1. 理解用户问题,并判断用户意图
2. 根据用户意图调用联网搜索,查询文档库,查询收件人信息
3. 编写邮件后,展示给用户,得到用户同意后发送邮件
4. 根据上述节点结果,判断是否继续循环,或者结束循环
'''

# 1. 定义共享内存
class AgentClassification(TypedDict):
    '''
        报告助手分类结果
    '''
    intent: Literal["web_search", "document_query", "send_email"]
    query: str | None

class AgentState(TypedDict):
    '''
        报告助手共享内存
    '''
    # 
    email_content: str
    sender_email: str
    email_id: str

    # 意图判断结果
    classification: AgentClassification | None

    # 工作节点结果
    web_result: dict | None  # 联网搜索结果
    document_result: dict | None # 查询文档库结果
    email_reciver: str | None # 收件人邮箱
    email_reciver_name: str | None # 收件人姓名
    email_content: str | None # 邮件内容

    # 响应结果
    draft_response: str | None

    # 消息列表
    messages: list[str] | None

# 2.初始化大语言模型
api_key = os.environ.get("MILK_NOTE_API_KEY")
model = ChatOpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    temperature=0.7
)

# 3.定义节点,langgraph中,每个节点是一个函数
def classify_intent(state: AgentState) -> dict:
    '''
        意图判断节点
    '''
    # 从状态中提取用户问题
    user_query = state["messages"][-1].content

    # 调用大语言模型进行意图判断
    model_with_structured_output = model.with_structured_output(AgentClassification)
    classification = model_with_structured_output.invoke(
        [
            HumanMessage(
                content=f"请判断用户问题的意图: {user_query},可以是联网搜索(web_search),查询文档库(document_query),或者发送邮件(send_email),以json格式返回"
            )
        ])
    print(f"意图判断结果: {classification}")
    if classification['intent'] == 'web_search':
        goto = "use_tools"
    elif classification['intent'] == 'document_query':
        goto = "search_documentation"
    elif classification['intent'] == 'send_email':
        goto = "query_email_reciver"
    else:
        goto = "draft_response"
    
    return Command(
        update={"classification": classification},# 更新状态,将分类结果添加到状态中
        goto= goto # 跳转下一个节点
    )

@tool
def use_web_search_tool(key_words: str) -> str:
    '''
        联网搜索工具

        args:
            key_words: 联网搜索关键词
    '''
    print(f"联网搜索关键词: {key_words}")
    return f"联网搜索关键词: {key_words},搜索答案是:{key_words}是个好东西。"

def use_tools(state: AgentState) -> dict:
    '''
        联网搜索节点
    '''
    # 从状态中提取用户问题
    user_query = state["messages"][-1].content
    agent = create_agent(model=model, tools=[use_web_search_tool],system_prompt="You are a helpful assistant")
    web_result = agent.invoke( {"messages": [{"role": "user", "content": user_query}]} )
    print(f"联网搜索结果: {web_result}")
    return Command(
        update={"web_result": web_result},# 更新状态,将联网搜索结果添加到状态中
        goto= "draft_response" # 跳转下一个节点
    )

def query_doc(query: str) -> str:
    '''
        查询文档库工具
        模拟通过sql like查询文档库
        args:
            query: 查询文档库关键词
    '''
    if("三国演义" in query):
        return "《三国演义》是中国古代的一部小说,作者是施耐庵。"
    elif("水浒传" in query):
        return "水浒传是中国古代的一部小说,作者是罗贯中。"
    elif("西游记" in query):
        return "西游记是中国古代的一部小说,作者是曹雪芹。"
    elif("红楼梦" in query):
        return "《红楼梦》是中国古代的一部小说,作者是吴承恩。"
    else:
        return f"查询文档库关键词: {query},文档库中没有相关内容。"

def search_documentation(state: AgentState) -> dict:
    '''
        查询文档库节点
    '''
    # 从状态中提取用户问题
    user_query = state["messages"][-1].content
    # 查询文档库
    document_result = query_doc(user_query)
    return Command(
        update={"document_result": document_result},# 更新状态,将查询文档库结果添加到状态中
        goto= "draft_response" # 跳转下一个节点
    )

def query_email_reciver(state: AgentState) -> dict:
    '''
        查询收件人邮箱节点
    '''
    # 从状态中提取用户问题
    user_list = [{
        "name": "张三",
        "email": "zhangsan@example.com"
    },{
        "name": "李四",
        "email": "lisi@example.com"
    },{
        "name": "王五",
        "email": "wangwu@example.com"
    },{
        "name": "赵六",
        "email": "zhaoliu@example.com"
    }]
    user_query = state["messages"][-1].content

    # 如果query包含用户姓名,则根据姓名查询邮箱
    goto = "draft_response"
    if any(user["name"] in user_query for user in user_list):
        user_info = next(user for user in user_list if user["name"] in user_query)
        goto = "human_review"
        user_query = state["messages"][-1].content
        # 调用大语言模型生成邮件内容
        email_content = model.invoke(f"你是一个优秀的个人助手,请你根据用户问题:{user_query}生成一封邮件内容,收件人是{user_info['name']}({user_info['email']})")
        return Command(
            update={"human_review": user_info["email"],"email_reciver_name": user_info["name"],"email_content": email_content,"email_reciver": user_info["email"]},# 更新状态,将查询收件人邮箱结果添加到状态中
            goto= goto # 跳转下一个节点
        )
    else:
        return Command(goto = END)
    
def human_review(state: AgentState) -> dict:
    '''
        人类审核节点
    '''
    # 从状态中提取用户问题
    human_opt =  interrupt({
        "query": state["messages"][-1].content,
        "email_reciver": state["email_reciver"],
        "email_reciver_name": state["email_reciver_name"],
        "email_content": state["email_content"],
    })
    
    print(f"人类审核结果: {human_opt}") 

    if human_opt.get("command") == "accept":
        goto = "draft_response"
    else:
        goto = END

    return Command(
        update={},
        goto=goto # 中断发送邮件节点
    )

def draft_response(state: AgentState) -> dict:
    '''
        草稿回复节点
    '''
    draft_response = model.invoke(f"你是一个优秀的个人助手,现在需要你根据agent执行状态:{state}生成一封草稿回复")
    print(f"草稿回复节点状态: {draft_response}")
    return Command(
        update={},# 更新状态,将草稿回复添加到状态中
        goto= END # 跳转下一个节点
    )

# 4.搭建工作流
agent_builder = StateGraph(AgentState)

# 添加节点
agent_builder.add_node("classify_intent", classify_intent)
agent_builder.add_node("use_tools", use_tools)
agent_builder.add_node("search_documentation", search_documentation)
agent_builder.add_node("query_email_reciver", query_email_reciver)
agent_builder.add_node("human_review", human_review)
agent_builder.add_node("draft_response", draft_response)

# 构建关系
agent_builder.add_edge(START, "classify_intent")
agent_builder.add_edge("draft_response", END)

# 完成工作流
# 注意 此处需要设置checkpointer,作为发送邮件前人工介入的前置条件
agent = agent_builder.compile(checkpointer=MemorySaver())

# 展示工作流
from IPython.display import Image, display
display(Image(agent.get_graph(xray=True).draw_mermaid_png()))

# 执行工作流
from langchain.messages import HumanMessage
messages = [HumanMessage(content="帮我发一封邮件给张三,内容是: 你好,张三,这是一封测试邮件。")]
thread_config = {"configurable": {"thread_id": "customer_123"}}
result = agent.invoke({"messages": messages},thread_config)

# 到此处,agent进入了人类审核节点
if(result['__interrupt__']):
    print(f"进入人类审核节点,审核内容:{result['__interrupt__']}")
    human_response = Command(
    resume={
        "command": "accept"
        }
    )
    result = agent.invoke(human_response,thread_config)
else:
    print("未进入人类审核节点")

for m in result["messages"]:
    m.pretty_print()