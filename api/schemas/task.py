from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, BeforeValidator

# 自定义验证器，将空字符串转换为None
def empty_str_to_none(v: Optional[str]) -> Optional[Any]:
    if v == "" or v is None:
        return None
    return v

# Pydantic模型
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: Optional[str] = "not_started"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    type: str

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class TaskInstanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class KRCreate(BaseModel):
    okr_id: int
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    current_value: float = 0
    status: Optional[str] = "not_started"

class KRUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None

class KRTaskCreate(BaseModel):
    kr_id: int
    task_id: int

# 响应模型
class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    once_task: Optional[Any] = None
    recurring_task: Optional[Any] = None

    class Config:
        from_attributes = True

class TaskInstanceResponse(BaseModel):
    id: int
    recurring_task_id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KRResponse(BaseModel):
    id: int
    okr_id: int
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    current_value: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KRTaskResponse(BaseModel):
    id: int
    kr_id: int
    task_id: int

    class Config:
        from_attributes = True
