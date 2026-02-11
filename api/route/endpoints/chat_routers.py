from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated
from api.models.user_models import User
from api.core.auth import get_current_active_user
from api.core.database import get_db
from api.core import logger
from api.services.chat_service import ChatService
from api.schemas import ChatMessage

router = APIRouter(prefix="/chat", tags=["聊天"])

@router.post("/send")
async def send_message(
    message: ChatMessage,
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """发送聊天消息"""
    logger.info(f"用户 {user.id} 发送消息: {message.input}")
    
    chat_service = ChatService(user_id=user.id, db=db)
    # 使用StreamingResponse处理异步生成器
    return StreamingResponse(chat_service.chat(message.input), media_type="text/event-stream")

@router.get("/history")
async def get_chat_history(
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    page_size: int = 10
):
    """获取聊天记录分页"""
    logger.debug(f"用户 {user.id} 请求聊天记录分页: 第{page}页, 每页{page_size}条")
    
    chat_service = ChatService(user_id=user.id, db=db)
    history = chat_service.get_history_page(page=page, page_size=page_size)
    
    return {"page": page, "page_size": page_size, "history": history}