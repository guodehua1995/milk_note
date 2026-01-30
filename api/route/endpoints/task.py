from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.auth import get_current_user
from api.models.user import User
from api.models.task import Task, TaskInstance, KR
from api.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse,
    TaskInstanceUpdate, TaskInstanceResponse,
    KRCreate, KRUpdate, KRResponse,
    KRTaskCreate, KRTaskResponse
)
from api.services.task_service import (
    create_task, get_tasks, get_task, update_task, delete_task,
    create_kr, update_kr, delete_kr
)

router = APIRouter()

# 统一事项路由
@router.post("/tasks", response_model=TaskResponse)
async def create_new_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新事项"""
    return create_task(db, task, current_user.id)

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    task_type: Optional[str] = Query(None, description="事项类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的所有事项"""
    return get_tasks(db, current_user.id, task_type)

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def retrieve_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定事项详情"""
    return get_task(db, task_id, current_user.id)

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_existing_task(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新事项"""
    return update_task(db, task_id, task, current_user.id)

@router.delete("/tasks/{task_id}")
async def delete_existing_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除事项"""
    return delete_task(db, task_id, current_user.id)


# KR路由
@router.post("/krs", response_model=KRResponse)
async def create_new_kr(
    kr: KRCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建KR"""
    return create_kr(db, kr, current_user.id)

@router.put("/krs/{kr_id}", response_model=KRResponse)
async def update_existing_kr(
    kr_id: int,
    kr: KRUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新KR"""
    return update_kr(db, kr_id, kr, current_user.id)

@router.delete("/krs/{kr_id}")
async def delete_existing_kr(
    kr_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除KR"""
    return delete_kr(db, kr_id, current_user.id)
