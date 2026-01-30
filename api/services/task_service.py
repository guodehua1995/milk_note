from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException
from api.models.task import KRTaskInstance, Task, TaskInstance, KR
from api.schemas.task import (
    TaskCreate, TaskUpdate,
    KRCreate, KRUpdate,

)

# 统一事项服务
def create_task(db: Session, task: TaskCreate, user_id: int) -> Task:
    """创建新事项"""
    db_task = Task(
        user_id=user_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        start_time=task.start_time,
        end_time=task.end_time,
        type=task.type
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_tasks(db: Session, user_id: int, task_type: Optional[str] = None) -> List[Task]:
    """获取用户的所有事项"""
    query = db.query(Task).filter(Task.user_id == user_id)
    if task_type:
        query = query.filter(Task.type == task_type)
    return query.all()

def get_task(db: Session, task_id: int, user_id: int) -> Task:
    """获取指定事项详情"""
    task = db.query(Task).filter(and_(Task.id == task_id, Task.user_id == user_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

def update_task(db: Session, task_id: int, task: TaskUpdate, user_id: int) -> Task:
    """更新事项"""
    db_task = get_task(db, task_id, user_id)
    update_data = task.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int, user_id: int) -> dict:
    """删除事项"""
    db_task = get_task(db, task_id, user_id)
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}

# KR服务
def create_kr(db: Session, kr: KRCreate, user_id: int) -> KR:
    """创建KR"""
    # 验证OKR存在且属于当前用户
    okr = db.query(Task).filter(and_(Task.id == kr.task_id, Task.user_id == user_id)).first()
    if not okr:
        raise HTTPException(status_code=404, detail="OKR not found")
    
    db_kr = KR(
        okr_id=kr.okr_id,
        title=kr.title,
        description=kr.description,
        target_value=kr.target_value,
        current_value=kr.current_value,
        status=kr.status
    )
    db.add(db_kr)
    db.commit()
    db.refresh(db_kr)
    return db_kr

def get_krs(db: Session, user_id: int, task_id: Optional[int] = None) -> List[KR]:
    """获取KR列表"""
    query = db.query(KR).join(Task).filter(Task.user_id == user_id)
    if task_id:
        query = query.filter(KR.task_id == task_id)
    return query.all()

def update_kr(db: Session, kr_id: int, kr: KRUpdate, user_id: int) -> KR:
    """更新KR"""
    db_kr = db.query(KR).join(Task).filter(
        and_(KR.id == kr_id, Task.user_id == user_id)
    ).first()
    if not db_kr:
        raise HTTPException(status_code=404, detail="KR not found")
    
    update_data = kr.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_kr, field, value)
    db.commit()
    db.refresh(db_kr)
    return db_kr

def delete_kr(db: Session, kr_id: int, user_id: int) -> dict:
    """删除KR"""
    db_kr = db.query(KR).join(Task).filter(
        and_(KR.id == kr_id, Task.user_id == user_id)
    ).first()
    if not db_kr:
        raise HTTPException(status_code=404, detail="KR not found")
    
    db.delete(db_kr)
    db.commit()
    return {"message": "KR deleted successfully"}

