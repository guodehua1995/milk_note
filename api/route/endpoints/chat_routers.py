import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated, AsyncGenerator
from api.models.user_models import User
from api.models import ChatHistory
from api.core.auth import get_current_active_user
from api.core.database import get_db
from api.core import logger
from api.services.chat_service import ChatService
from api.schemas import ChatMessage
from api.agents import MainAgent, TaskChatAgent
from langchain_core.messages.ai import AIMessageChunk

router = APIRouter(prefix="/chat", tags=["聊天"])

async def format_stream_message(message, meta_data) -> dict:
    '''
        格式化消息
    '''
    # 如果是AIMessageChunk
    if isinstance(message, AIMessageChunk):
        # 工具调用消息
        if(len(message.tool_calls) > 0):
            tool_names = []
            for tool_call in message.tool_calls:
                tool_names.append(tool_call['name'])
            return {"type": "tool", "content": f"调用工具: {', '.join(tool_names)}"}
        else:
            # 检查meta_data中是否存在tags键，避免KeyError
            if meta_data.get("tags") and "stream_to_user" in meta_data["tags"]:
                return {"type": "assistant", "content": message.content or ""}
            else:
                return {"type": "assistant", "content": ""}

    return {"type": "assistant", "content": ""}

@router.post("/send")
async def send_message(
    message: ChatMessage,
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """发送聊天消息"""
    logger.info(f"用户 {user.id} 发送消息: {message.input}")
    
    async def generate_response() -> AsyncGenerator[str, None]:
        # 发送开始消息
        yield json.dumps({"type": "start", "content": "模型正在思考..."}, ensure_ascii=False) + '\n'
        
        try:
            # 创建聊天记录
            chat_service = ChatService(user_id=user.id, db=db)
            chat_id = chat_service.create_chat_history(message.input, "user")
            
            # 获取聊天历史
            history = chat_service.get_history_page()
            
            # 使用MainAgent处理聊天
            main_agent = MainAgent()
            assistant_message = ""
            
            # 处理流式响应
            for m, meta_data in main_agent.agent_stream(message.input, history, user.id, None):
                formatted_message = await format_stream_message(m, meta_data)
                assistant_message += formatted_message["content"]
                yield json.dumps(formatted_message, ensure_ascii=False) + '\n'
            
            # 发送结束消息
            yield json.dumps({"type": "end", "content": "模型思考结束"}, ensure_ascii=False) + '\n'
            
            # 保存助手回复
            chat_service.create_chat_history(assistant_message, "assistant", chat_id)
        except Exception as e:
            logger.error(f"聊天处理异常: {str(e)}", exc_info=True)
            error_message = "回答中出现了一些意料之外的问题,请稍后重试~"
            yield json.dumps({"type": "assistant", "content": error_message}, ensure_ascii=False) + '\n'
            yield json.dumps({"type": "end", "content": "模型思考结束"}, ensure_ascii=False) + '\n'
    
    # 使用StreamingResponse处理异步生成器
    return StreamingResponse(generate_response(), media_type="text/event-stream")

@router.post("/task/send")
async def send_task_message(
    task_id: int,
    message: ChatMessage,
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """发送任务相关消息"""
    logger.info(f"用户 {user.id} 发送任务消息: {message.input}")
    
    async def generate_response() -> AsyncGenerator[str, None]:
        # 发送开始消息
        yield json.dumps({"type": "start", "content": "模型正在思考..."}, ensure_ascii=False) + '\n'
        
        try:
            # 创建聊天记录
            chat_service = ChatService(user_id=user.id, db=db)
            chat_id = chat_service.create_chat_history(message.input, "user")
            
            # 使用TaskChatAgent处理任务聊天
            task_agent = TaskChatAgent(user.id, task_id)
            assistant_message = ""
            
            # 处理流式响应
            for m, meta_data in task_agent.ask_stream(message.input):
                formatted_message = await format_stream_message(m, meta_data)
                assistant_message += formatted_message["content"]
                yield json.dumps(formatted_message, ensure_ascii=False) + '\n'
            
            # 发送结束消息
            yield json.dumps({"type": "end", "content": "模型思考结束"}, ensure_ascii=False) + '\n'
            
            # 保存助手回复
            chat_service.create_chat_history(assistant_message, "assistant", chat_id)
        except Exception as e:
            logger.error(f"任务聊天处理异常: {str(e)}", exc_info=True)
            error_message = "回答中出现了一些意料之外的问题,请稍后重试~"
            yield json.dumps({"type": "assistant", "content": error_message}, ensure_ascii=False) + '\n'
            yield json.dumps({"type": "end", "content": "模型思考结束"}, ensure_ascii=False) + '\n'
    
    # 使用StreamingResponse处理异步生成器
    return StreamingResponse(generate_response(), media_type="text/event-stream")

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