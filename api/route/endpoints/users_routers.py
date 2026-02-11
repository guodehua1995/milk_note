# api/api_v1/endpoints/users.py
from fastapi import APIRouter, Depends
from typing import Annotated

from api.core.auth import get_current_active_user
from api.models.user_models import User
from api.schemas.user import UserResponse  

router = APIRouter(prefix="/users", tags=["用户"])

@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    """获取当前登录用户信息（需要认证）"""
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)]
)-> UserResponse:
    """获取指定用户信息（需要认证）"""
    # 这里可以添加权限检查，比如只允许管理员或自己查看
    # ...
    return None