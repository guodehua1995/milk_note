import os
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())
from langchain_community.llms import Tongyi
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from fastapi import FastAPI
from langserve import add_routes

# 从环境变量中获取API密钥，如果没有设置则使用默认值
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-fdf9e8d52ffa4641a68fea1094988c02")

def log(llm_result:str):
    print("i got it"+llm_result)

# 检查API密钥是否存在
if not DASHSCOPE_API_KEY:
    raise ValueError("请设置DASHSCOPE_API_KEY环境变量")

# 将dashscope_api_key参数移到Tongyi类的初始化中
llm=Tongyi(temperature=1, dashscope_api_key=DASHSCOPE_API_KEY)
template='''
        你的名字是小黑子,当人问问题的时候,你都会在开头加上'唱,跳,rap,篮球!',然后再回答{question}
    '''
prompt=PromptTemplate(
        template=template,
        input_variables=["question"]#这个question就是用户输入的内容,这行代码不可缺少
)
# 使用更现代的LangChain API替换已弃用的LLMChain
parser = StrOutputParser()
chain = prompt | llm | parser
question='你是谁'

# res=chain.invoke({"question": question})#运行

# print(res)#打印结果

# 4. App definition
app = FastAPI(
  title="LangChain Server",
  version="1.0",
  description="A simple API server using LangChain's Runnable interfaces",
)

add_routes(
    app,
    chain,
    path="/chain",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)