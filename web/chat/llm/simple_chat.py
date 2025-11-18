from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os

# 更安全地获取环境变量，如果不存在则提示错误
api_key = os.environ.get("MILK_NOTE_API_KEY")
if api_key is None:
    print("错误: 环境变量MILK_NOTE_API_KEY未设置")
    print("请确保在系统环境变量中设置了该变量，并重启终端")
    # 可以设置一个默认值用于测试，但生产环境不推荐
    # api_key = "默认测试密钥"
else:
    print(f"成功获取环境变量: {api_key}")
chatLLM = ChatOpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",  # 此处以qwen-plus为例，您可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    # other params...
)
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "你是谁？"}]
chatLLM.invoke([HumanMessage(content="Hi! I'm Bob")])


