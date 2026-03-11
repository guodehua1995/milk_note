from api.models import ChatHistory
from sqlalchemy.orm import Session
from api.core import get_logger
from typing import Optional
from langchain_core.messages import HumanMessage, AnyMessage

logger = get_logger(__name__)

class ChatService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def get_history_page(self, page: int = 1, page_size: int = 10) -> list[ChatHistory]:
        '''
        获取用户聊天记录分页
        '''
        return ChatHistory.get_history_page(self.db, self.user_id, page, page_size)[::-1]

    def create_chat_history(self, content: str, type: str, parent_id: Optional[int] = None) -> int:
        '''
        创建聊天记录
        '''
        return ChatHistory.create(self.db, self.user_id, content, type, parent_id)

    def __covert_history(self, historys: list[ChatHistory]) -> list[dict]:
        '''
        转换为消息列表
        '''
        return [{"role": h.type, "content": h.content, "timestamp": h.timestamp.strftime("%Y-%m-%d %H:%M:%S")} for h in historys]