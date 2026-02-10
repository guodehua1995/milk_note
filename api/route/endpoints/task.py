from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

from api.core.database import get_db
from api.core.auth import get_current_active_user
from api.models.user import User
from api.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskExecutionCreate, TaskExecutionUpdate, TaskExecutionResponse, TaskExecutionListResponse,
    BatchExecutionCreate, AIPlanResponse, ProgressResponse
)
from api.services.task import TaskService, TaskExecutionService
from api.core import logger


router = APIRouter(prefix="/tasks", tags=["任务"])


# 任务相关路由
@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    创建任务
    
    - **title**: 任务标题
    - **description**: 任务描述
    - **task_type**: 任务类型（once/repeat/complex）
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **repeat_cycle**: 重复周期（仅重复任务需要）
    - **is_ai_planned**: 是否开启AI规划
    - **parent_id**: 父任务ID（仅子任务需要）
    - **document_ids**: 绑定的文档ID列表，用逗号分隔
    """
    try:
        task_service = TaskService(db, current_user.id)
        task = task_service.create_task(
            title=task_data.title,
            description=task_data.description,
            task_type=task_data.task_type,
            start_date=task_data.start_date,
            end_date=task_data.end_date,
            repeat_cycle=task_data.repeat_cycle,
            is_ai_planned=task_data.is_ai_planned,
            parent_id=task_data.parent_id,
            document_ids=task_data.document_ids
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建任务失败")


@router.get("", response_model=TaskListResponse)
async def get_tasks(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    include_subtasks: bool = False
):
    """
    获取任务列表
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    - **include_subtasks**: 是否包含子任务
    """
    try:
        task_service = TaskService(db, current_user.id)
        tasks = task_service.get_tasks(skip=skip, limit=limit, include_subtasks=include_subtasks)
        total = len(tasks)
        return TaskListResponse(items=tasks, total=total)
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务列表失败")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_detail(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    获取任务详情
    
    - **task_id**: 任务ID
    """
    try:
        task_service = TaskService(db, current_user.id)
        task = task_service.get_task_detail(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务详情失败")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    更新任务
    
    - **task_id**: 任务ID
    - **title**: 任务标题（可选）
    - **description**: 任务描述（可选）
    - **task_type**: 任务类型（可选）
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    - **repeat_cycle**: 重复周期（可选）
    - **is_ai_planned**: 是否开启AI规划（可选）
    - **document_ids**: 绑定的文档ID列表（可选）
    """
    try:
        task_service = TaskService(db, current_user.id)
        # 构建更新数据字典
        update_data = task_data.model_dump(exclude_unset=True)
        # 转换task_type字段名
        if "task_type" in update_data:
            update_data["type"] = update_data.pop("task_type")
        task = task_service.update_task(task_id, **update_data)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新任务失败")


@router.put("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    取消任务
    
    - **task_id**: 任务ID
    """
    try:
        task_service = TaskService(db, current_user.id)
        task = task_service.cancel_task(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="取消任务失败")


@router.get("/{task_id}/progress", response_model=ProgressResponse)
async def calculate_task_progress(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    计算任务进度
    
    - **task_id**: 任务ID
    """
    try:
        task_service = TaskService(db, current_user.id)
        progress = task_service.calculate_progress(task_id)
        # 获取更新后的任务状态
        task = task_service.get_task_detail(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
        return ProgressResponse(task_id=task_id, progress=progress, status=task.status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算任务进度失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="计算任务进度失败")


@router.post("/{task_id}/ai-plan", response_model=AIPlanResponse)
async def ai_plan_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    AI规划任务
    
    - **task_id**: 任务ID
    """
    try:
        task_service = TaskService(db, current_user.id)
        executions = task_service.ai_plan_task(task_id)
        return AIPlanResponse(
            success=True,
            message="AI规划成功",
            executions=executions
        )
    except Exception as e:
        logger.error(f"AI规划任务失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI规划任务失败")


# 执行情况相关路由
@router.post("/{task_id}/executions", response_model=TaskExecutionResponse, status_code=status.HTTP_201_CREATED)
async def create_execution(
    task_id: int,
    execution_data: TaskExecutionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    创建执行情况
    
    - **task_id**: 任务ID
    - **title**: 执行情况标题
    - **content**: 执行情况内容
    - **execution_date**: 执行日期
    """
    try:
        execution_service = TaskExecutionService(db, current_user.id)
        execution = execution_service.create_execution(
            task_id=task_id,
            title=execution_data.title,
            content=execution_data.content,
            execution_date=execution_data.execution_date
        )
        return execution
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"创建执行情况失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建执行情况失败")


@router.get("/{task_id}/executions", response_model=TaskExecutionListResponse)
async def get_executions(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    获取执行情况列表
    
    - **task_id**: 任务ID
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    """
    try:
        execution_service = TaskExecutionService(db, current_user.id)
        executions = execution_service.get_executions(task_id, skip=skip, limit=limit)
        total = len(executions)
        return TaskExecutionListResponse(items=executions, total=total)
    except Exception as e:
        logger.error(f"获取执行情况列表失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取执行情况列表失败")


@router.get("/executions/{execution_id}", response_model=TaskExecutionResponse)
async def get_execution_detail(
    execution_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    获取执行情况详情
    
    - **execution_id**: 执行情况ID
    """
    try:
        execution_service = TaskExecutionService(db, current_user.id)
        execution = execution_service.get_execution_detail(execution_id)
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行情况不存在")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取执行情况详情失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取执行情况详情失败")


@router.put("/executions/{execution_id}", response_model=TaskExecutionResponse)
async def update_execution(
    execution_id: int,
    execution_data: TaskExecutionUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    更新执行情况
    
    - **execution_id**: 执行情况ID
    - **title**: 执行情况标题（可选）
    - **content**: 执行情况内容（可选）
    - **status**: 执行情况状态（可选）
    - **execution_result**: 执行结果（可选）
    """
    try:
        execution_service = TaskExecutionService(db, current_user.id)
        update_data = execution_data.model_dump(exclude_unset=True)
        execution = execution_service.update_execution(execution_id, **update_data)
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行情况不存在")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新执行情况失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新执行情况失败")


@router.put("/executions/{execution_id}/cancel", response_model=TaskExecutionResponse)
async def cancel_execution(
    execution_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    取消执行情况
    
    - **execution_id**: 执行情况ID
    """
    try:
        execution_service = TaskExecutionService(db, current_user.id)
        execution = execution_service.cancel_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行情况不存在")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消执行情况失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="取消执行情况失败")


@router.post("/{task_id}/executions/batch", response_model=List[TaskExecutionResponse], status_code=status.HTTP_201_CREATED)
async def batch_create_executions(
    task_id: int,
    batch_data: BatchExecutionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    批量创建执行情况
    
    - **task_id**: 任务ID
    - **executions**: 执行情况列表，每个元素包含title、content、execution_date等字段
    """
    try:
        execution_service = TaskExecutionService(db, current_user.id)
        # 转换为字典列表
        executions_data = [execution.model_dump() for execution in batch_data.executions]
        executions = execution_service.batch_create_executions(task_id, executions_data)
        return executions
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"批量创建执行情况失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="批量创建执行情况失败")


@router.put("/executions/update-status", response_model=dict)
async def update_all_executions_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    更新所有执行情况的状态
    """
    try:
        execution_service = TaskExecutionService(db, current_user.id)
        updated_count = execution_service.update_all_executions_status()
        return {"updated_count": updated_count, "message": "执行情况状态更新成功"}
    except Exception as e:
        logger.error(f"更新所有执行情况状态失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新所有执行情况状态失败")
