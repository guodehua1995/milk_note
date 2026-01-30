'''
    路由模块
'''

from fastapi import APIRouter
from .endpoints import auth, users, chat, document, task

api_router = APIRouter()

# 注册认证路由
api_router.include_router(auth.router, prefix="/api", tags=["认证"])

# 注册用户路由
api_router.include_router(users.router, prefix="/api", tags=["用户"])

# 注册聊天路由
api_router.include_router(chat.router, prefix="/api", tags=["聊天"])

# 注册文档路由
api_router.include_router(document.router, prefix="/api", tags=["文档"])

# 注册任务路由
api_router.include_router(task.router, prefix="/api", tags=["任务"])
