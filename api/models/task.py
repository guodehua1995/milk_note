from sqlalchemy import ForeignKey, String, Text, Integer, Boolean, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from api.core import Base
from sqlalchemy.orm import Session
from typing import Optional

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # once/repeat/complex
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="not_started")  # not_started/in_progress/completed/cancelled
    context: Mapped[str] = mapped_column(Text, nullable=True)  # 目标上下文，用于AI规划待办事项
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    repeat_cycle: Mapped[str] = mapped_column(String(255), nullable=True)  # never/weekly:1,3,5/monthly:1,15,20
    is_ai_planned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 完成度，0-100
    parent_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=True)  # 父目标ID
    document_ids: Mapped[str] = mapped_column(Text, nullable=True)  # 绑定的文档ID列表，用逗号分隔
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", backref="tasks")
    parent = relationship("Task", remote_side=[id], backref="subtasks")
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")
    think_logs = relationship("TaskThinkLog", back_populates="task", cascade="all, delete-orphan")

    @classmethod
    def get_task_by_id(cls, db: Session, task_id: int):
        '''
        根据ID获取目标
        '''
        return db.query(cls).filter(cls.id == task_id).first()

    @classmethod
    def get_tasks_by_user_id(cls, db: Session, user_id: int, skip: int = 0, limit: int = 100):
        '''
        根据用户ID获取目标列表
        '''
        return db.query(cls).filter(cls.user_id == user_id).offset(skip).limit(limit).all()

    @classmethod
    def get_parent_tasks_by_user_id(cls, db: Session, user_id: int, skip: int = 0, limit: int = 100):
        '''
        根据用户ID获取父目标列表（不包含子目标）
        '''
        return db.query(cls).filter(cls.user_id == user_id, cls.parent_id.is_(None)).offset(skip).limit(limit).all()


class TaskExecution(Base):
    """
    执行单元表
    """
    __tablename__ = "task_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="not_started")  # not_started/in_progress/completed/cancelled/overdue
    summaried: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # 是否总结
    execution_date: Mapped[Date] = mapped_column(Date, nullable=False)
    execution_result: Mapped[str] = mapped_column(Text, nullable=True)  # 执行结果，支持最高2000字
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    task = relationship("Task", back_populates="executions")

    @classmethod
    def get_execution_by_id(cls, db: Session, execution_id: int):
        '''
        根据ID获取执行情况
        '''
        return db.query(cls).filter(cls.id == execution_id).first()

    @classmethod
    def get_executions_by_task_id(cls, db: Session, task_id: int, skip: int = 0, limit: int = 100):
        '''
        根据目标ID获取执行情况列表
        '''
        return db.query(cls).filter(cls.task_id == task_id).offset(skip).limit(limit).all()

    @classmethod
    def get_executions_by_user_id_and_date(cls, db: Session, user_id: int, execution_date: Date):
        '''
        根据用户ID和执行日期获取执行情况列表
        '''
        from sqlalchemy import and_
        return db.query(cls).join(Task).filter(
            and_(Task.user_id == user_id, cls.execution_date == execution_date)
        ).all()


class TaskThinkLog(Base):
    """
    任务思考日志
    """
    __tablename__ = "task_think_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # re_plan/
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 思考内容
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="think_logs")

    @classmethod
    def get_think_log_by_id(cls, db: Session, task_id: int, type: Optional[str] = None):
        '''
        根据ID获取思考日志
        '''
        query = db.query(cls).filter(cls.task_id == task_id)
        if type is not None:
            query = query.filter(cls.type == type)
        return query.first()
