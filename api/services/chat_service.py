import json
from langchain_core.messages.ai import AIMessageChunk
from api.models import ChatHistory
from sqlalchemy.orm import Session
from api.core import logger
from .agents.main_agent import MainAgent
from api.services.tools import TOOL_NAME

class ChatService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.agent = MainAgent(user_id)


    def get_history_page(self, page: int = 1, page_size: int = 10) -> list[ChatHistory]:
        '''
        获取用户聊天记录分页
        '''
        return ChatHistory.get_history_page(self.db, self.user_id, page, page_size)[::-1]

    async def chat(self, input: str):
        '''
        执行主智能体工作流
        '''
        # 将字典转换为JSON字符串
        yield json.dumps({"type": "start", "content": "模型正在思考..."}, ensure_ascii=False)
        assistant_message = ""
        chat_id = ChatHistory.create(self.db, self.user_id, input, "user")
        # 执行智能体并流式返回执行结果
        # agent_stream返回的是元组(message, is_last)
        for m, _ in self.agent.agent_stream(input):
            message = self.__format_stream_message(m)
            assistant_message += message["content"]
            # 将字典转换为JSON字符串，确保中文字符不被转义
            yield json.dumps(message, ensure_ascii=False)+'\n'
        
        # 将字典转换为JSON字符串
        yield json.dumps({"type": "end", "content": "模型思考结束"}, ensure_ascii=False)
        ChatHistory.create(self.db,self.user_id, assistant_message, "assistant", chat_id)

    def __format_stream_message(self, message) -> dict:
        '''
            格式化消息
        '''
        # 如果是AIMessageChunk
        if isinstance(message, AIMessageChunk):
            # 工具调用消息
            if(len(message.tool_calls) > 0):
                tool_names = []
                for tool_call in message.tool_calls:
                    tool_names.append( TOOL_NAME.get(tool_call["name"], '工具'))
                return {"type": "assistant", "content": f"调用工具: {', '.join(tool_names)}"}
            else:
                return {"type": "assistant", "content": message.content or ""}
        
        return {"type": "assistant", "content": message.content or ""}
