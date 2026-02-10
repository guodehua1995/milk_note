"""
项目常量定义文件
集中管理所有模型状态、类型等常量和枚举
"""

from enum import Enum


# 文档处理状态枚举
class DocumentStatus(str, Enum):
    """RagDocument状态枚举"""
    PENDING = "not_started"  # 未开始
    EMBEDDING = "embedding"  # 向量生成中
    COMPLETED = "completed"  # 处理完成
    FAILED = "failed"  # 处理失败


# 文档切片状态枚举
class ChunkStatus(str, Enum):
    """RagChunks状态枚举"""
    PENDING = "pending"  # 待处理
    COMPLETED = "completed"  # 处理完成
    FAILED = "failed"  # 处理失败


# 文档类型枚举
class DocumentType(str, Enum):
    """文档类型枚举"""
    PDF = "pdf"  # PDF文档
    DOCX = "docx"  # Word文档
    TXT = "txt"  # 文本文件
    MD = "md"  # Markdown文件


# 任务状态枚举
class TaskStatus(str, Enum):
    """通用任务状态枚举"""
    PENDING = "not_started"  # 未开始
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


# 目标类型枚举
class TaskType(str, Enum):
    """目标类型枚举"""
    ONCE = "once"  # 一次性目标
    REPEAT = "repeat"  # 重复目标
    COMPLEX = "complex"  # 复杂目标


# 目标状态枚举
class GoalStatus(str, Enum):
    """目标状态枚举"""
    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


# 执行情况状态枚举
class ExecutionStatus(str, Enum):
    """执行情况状态枚举"""
    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    OVERDUE = "overdue"  # 已超时


# 用户角色枚举
class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"  # 管理员
    USER = "user"  # 普通用户


# 向量维度常量
VECTOR_DIMENSION = 1536  # 默认向量维度

# 文档切片配置
CHUNK_SIZE = 2000  # 默认切片大小
CHUNK_OVERLAP = 100  # 默认切片重叠大小

# 定时任务配置
DOCUMENT_PROCESS_INTERVAL = 60  # 文档处理间隔（秒）
