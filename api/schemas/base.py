from pydantic import BaseModel, EmailStr
from typing import Generic, TypeVar

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    """
    基础响应模型。
    """
    success: int = 0
    message: str = "success"
    data: T | None = None