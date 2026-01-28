from calendar import c
import json
from langchain_core.messages.ai import AIMessageChunk
from api.models import ChatHistory
from sqlalchemy.orm import Session
from api.core import get_logger
from .agents.main_agent import MainAgent
from api.services.tools import TOOL_NAME, TOOL_INFO

logger = get_logger(__name__)

class ChatService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.agent = MainAgent()


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
        for m, meta_data in self.agent.agent_stream(input,self.user_id):
            message = self.__format_stream_message(m,meta_data)
            assistant_message += message["content"]
            # 将字典转换为JSON字符串，确保中文字符不被转义
            yield json.dumps(message, ensure_ascii=False)+'\n'
        
        # 将字典转换为JSON字符串
        yield json.dumps({"type": "end", "content": "模型思考结束"}, ensure_ascii=False)
        logger.debug(f"保存聊天记录{assistant_message}")
        ChatHistory.create(self.db,self.user_id, assistant_message, "assistant", chat_id)

    def __format_stream_message(self, message, meta_data) -> dict:
        '''
            格式化消息
        '''
        #logger.info("agent消息处理器收到消息：%s, 元数据：%s", message, meta_data)
        # 如果是AIMessageChunk
        if isinstance(message, AIMessageChunk):
            # 工具调用消息
            if(len(message.tool_calls) > 0):
                tool_names = []
                for tool_call in message.tool_calls:
                    # logger.debug(f"工具调用节点,当前工具调用:{tool_call}")
                    if tool_call['name'] in TOOL_INFO:
                        tool_names.append( TOOL_INFO.get(tool_call["name"]).tool_name)  
                return {"type": "tool", "content": f"调用工具: {', '.join(tool_names)}"}
            else:
                # 检查meta_data中是否存在tags键，避免KeyError
                if meta_data.get("tags") and "stream_to_user" in meta_data["tags"]:
                    return {"type": "assistant", "content": message.content or ""}
                else:
                    return {"type": "assistant", "content": ""}

        return {"type": "assistant", "content": ""}
