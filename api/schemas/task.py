from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


# 任务相关Schema
class TaskBase(BaseModel):
    """任务基础模型"""
    title: str = Field(..., description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    task_type: str = Field(..., description="任务类型（once/repeat/complex）")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    repeat_cycle: Optional[str] = Field(None, description="重复周期（仅重复任务需要）")
    is_ai_planned: bool = Field(False, description="是否开启AI规划")
    parent_id: Optional[int] = Field(None, description="父任务ID（仅子任务需要）")
    document_ids: Optional[str] = Field(None, description="绑定的文档ID列表，用逗号分隔")


class TaskCreate(TaskBase):
    """创建任务模型"""
    pass


class TaskUpdate(BaseModel):
    """更新任务模型"""
    title: Optional[str] = Field(None, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    task_type: Optional[str] = Field(None, description="任务类型")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    repeat_cycle: Optional[str] = Field(None, description="重复周期")
    is_ai_planned: Optional[bool] = Field(None, description="是否开启AI规划")
    document_ids: Optional[str] = Field(None, description="绑定的文档ID列表")


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: int
    user_id: int
    title: str
    description: Optional[str]
    type: str
    status: str
    context: Optional[str]
    start_date: date
    end_date: date
    repeat_cycle: Optional[str]
    is_ai_planned: bool
    progress: int
    parent_id: Optional[int]
    document_ids: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    items: List[TaskResponse]
    total: int


# 执行情况相关Schema
class TaskExecutionBase(BaseModel):
    """执行情况基础模型"""
    title: str = Field(..., description="执行情况标题")
    content: Optional[str] = Field(None, description="执行情况内容")
    execution_date: Optional[date] = Field(None, description="执行日期")


class TaskExecutionCreate(TaskExecutionBase):
    """创建执行情况模型"""
    pass


class TaskExecutionUpdate(BaseModel):
    """更新执行情况模型"""
    title: Optional[str] = Field(None, description="执行情况标题")
    content: Optional[str] = Field(None, description="执行情况内容")
    status: Optional[str] = Field(None, description="执行情况状态")
    execution_result: Optional[str] = Field(None, description="执行结果")


class TaskExecutionResponse(BaseModel):
    """执行情况响应模型"""
    id: int
    task_id: int
    title: str
    content: Optional[str]
    status: str
    execution_date: date
    execution_result: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskExecutionListResponse(BaseModel):
    """执行情况列表响应模型"""
    items: List[TaskExecutionResponse]
    total: int


# 批量创建执行情况模型
class BatchExecutionCreate(BaseModel):
    """批量创建执行情况模型"""
    executions: List[TaskExecutionCreate]


# AI规划响应模型
class AIPlanResponse(BaseModel):
    """AI规划响应模型"""
    success: bool
    message: str
    executions: Optional[List[TaskExecutionResponse]] = None


# 进度响应模型
class ProgressResponse(BaseModel):
    """进度响应模型"""
    task_id: int
    progress: int
    status: str
