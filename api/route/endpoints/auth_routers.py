# api/api_v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional

from api.core.config import settings
from api.core.database import get_db
from api.core.auth import create_access_token
from api.models.user_models import User
from api.schemas.auth import Token, UserCreate, UserLogin
from api.core import logger
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    用户登录，返回JWT访问令牌
    支持 OAuth2.0 密码授权类型和 JSON 格式
    
    - **username**: 用户名
    - **password**: 密码
    """
    login_username = None
    login_password = None
    
    content_type = request.headers.get("Content-Type")
    
    if content_type and "application/json" in content_type:
        # 处理 JSON 请求
        try:
            user_login = await request.json()
            login_username = user_login.get("username")
            login_password = user_login.get("password")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的 JSON 格式",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        # 处理表单请求
        try:
            form_data = await request.form()
            login_username = form_data.get("username")
            login_password = form_data.get("password")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的请求格式",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # 验证用户名和密码是否存在
    if not login_username or not login_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供用户名和密码",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证用户名和密码
    user = User.get_user_by_username(db, username=login_username)
    if not user or not user.verify_password(login_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},  # sub字段符合 OAuth2.0 标准，用于存储用户标识符
        expires_delta=access_token_expires
    )
    
    logger.debug(f"用户 {user.username} 登录成功")
    
    # 返回符合 OAuth2.0 标准的响应格式
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 检查用户名是否已存在
    if User.get_user_by_username(db, username=user_data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建新用户
    user = User(
        username=user_data.username,
        email=user_data.email
    )
    logger.debug(f"创建用户：{user.username},密码:{user_data.password}")
    user.set_password(user_data.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"msg": "用户注册成功"}