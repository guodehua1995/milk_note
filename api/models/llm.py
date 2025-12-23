from typing import List,Optional
from sqlalchemy import ForeignKey,String
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from api.core import Base
from datetime import datetime
from sqlalchemy.orm import Session


class ChatHistory(Base):
    '''
    聊天记录模型
        存储用户与助手的交互记录
    '''

    __tablename__ = "chat_histories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    # 所属用户id
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # 发送内容
    content: Mapped[str] = mapped_column(String(128), nullable=False)
    # 发送时间
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)
    # 消息类型 用户消息/工具消息/系统消息/助手消息
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    # 回复消息id
    reply_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chat_histories.id"), nullable=True)


    @classmethod
    def create(cls,db:Session, user_id:int,content:str,type:str,reply_id:Optional[int]=None) -> int:
        '''
        创建聊天记录
        '''
        chat_history = cls(
            user_id=user_id,
            content=content,
            type=type,
            reply_id=reply_id
        )
        db.add(chat_history)
        db.commit()
        db.refresh(chat_history)
        return chat_history.id

    @classmethod
    def get_history_page(cls, db: Session, user_id: int, page: int = 1, page_size: int = 10) -> List["ChatHistory"]:
        '''
        获取用户聊天记录分页
        '''
        return db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id
        ).order_by(
            ChatHistory.timestamp.desc()
        ).offset(
            (page-1)*page_size
        ).limit(
            page_size
        ).all()