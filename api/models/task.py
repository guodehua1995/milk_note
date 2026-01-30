from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Date, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from api.core.database import Base

class Task(Base):
    """统一事项模型"""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started/in_progress/completed/cancelled/overdue
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low/medium/high
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # once/recurring/okr
    recurrence_type: Mapped[str] = mapped_column(String(20), default="never")  # never/daily/weekly/monthly/yearly
    recurrence_interval: Mapped[int] = mapped_column(Integer, default=1)
    recurrence_rule: Mapped[str] = mapped_column(String(255), nullable=False)  # 字符串格式的重复规则
    recurrence_end_type: Mapped[str] = mapped_column(String(20), default="never")  # never/on_date/after_occurrences
    recurrence_occurrences: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    user = relationship("User", backref="tasks")
    task_instances = relationship("TaskInstance", back_populates="task", cascade="all, delete-orphan")
    kr_tasks = relationship("KRTaskInstance", back_populates="task", cascade="all, delete-orphan")

class TaskInstance(Base):
    """重复事项实例模型"""
    __tablename__ = "task_instances"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recurring_task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started/in_progress/completed/cancelled/overdue
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    task = relationship("Task", back_populates="task_instances")
    kr_tasks = relationship("KRTaskInstance", back_populates="task_instance", cascade="all, delete-orphan")
    krs = relationship("KR", secondary="kr_tasks_instances", back_populates="task_instances")

class KR(Base):
    """关键结果模型"""
    __tablename__ = "krs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    target_value: Mapped[float] = mapped_column(Float, nullable=True)
    current_value: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started/in_progress/completed/cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    task = relationship("Task", back_populates="krs")
    kr_tasks_instances = relationship("KRTaskInstance", back_populates="kr", cascade="all, delete-orphan")
    task_instances = relationship("TaskInstance", secondary="kr_tasks_instances", back_populates="krs")

class KRTaskInstance(Base):
    """KR与事项关联模型"""
    __tablename__ = "kr_tasks_instances"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    kr_id: Mapped[int] = mapped_column(ForeignKey("krs.id"), nullable=False)
    task_instance_id: Mapped[int] = mapped_column(ForeignKey("task_instances.id"), nullable=False)

    # 关联
    kr = relationship("KR", back_populates="kr_tasks")
    task = relationship("Task", back_populates="kr_tasks")
    task_instance = relationship("TaskInstance", back_populates="kr_tasks")
