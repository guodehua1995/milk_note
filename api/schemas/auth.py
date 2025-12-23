# api/api_v1/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional

# 登录请求模型
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 登录请求模型
class UserLogin(BaseModel):
    username: str
    password: str

# 注册请求模型（可选）
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str