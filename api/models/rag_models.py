from typing import List, Optional, Dict, Any
from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from api.core import Base
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

class RagDocument(Base):
    """
    知识库文档表
    """
    __tablename__ = "rag_documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="知识库文档ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="用户ID")
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=True, comment="事项ID")
    type: Mapped[str] = mapped_column(String(20), default="pdf", comment="文档类型")
    file_name: Mapped[str] = mapped_column(String(255), comment="文档名称")
    file_key: Mapped[str] = mapped_column(String(255), comment="文档路径")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, comment="更新时间")
    delete_at: Mapped[Optional[datetime]] = mapped_column(comment="删除时间")
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="状态 failed/pending/splited/embedding/completed")
    is_deleted: Mapped[bool] = mapped_column(default=False, comment="是否删除")
    
    # 关系：一个文档对应多个切片
    chunks: Mapped[List["RagChunks"]] = relationship(
        "RagChunks", back_populates="document", cascade="all, delete-orphan"
    )

class RagChunks(Base):
    """
    文档切片表
    用于存储RAG应用中文档切片后的原文和向量数据
    """
    __tablename__ = "rag_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="知识库文档切片ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="用户ID")
    document_id: Mapped[str] = mapped_column(ForeignKey("rag_documents.id"), comment="知识库文档ID")
    task_id: Mapped[str] = mapped_column(String(36), comment="事项ID")
    content: Mapped[str] = mapped_column(String(5000), comment="文档切片内容")
    vector: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True, comment="文本向量(1536维)")  # 使用pgvector的Vector类型，允许暂时为空
    path: Mapped[str] = mapped_column(String(255), comment="文档路径")
    metadata_: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, comment="文档元数据", name="metadata")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, comment="更新时间")
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="状态")
    
    # 关系：多个切片对应一个文档
    document: Mapped["RagDocument"] = relationship("RagDocument", back_populates="chunks")
    
    @classmethod
    def create_chunk(cls, db: Session, **kwargs) -> "RagChunks":
        """
        创建文档切片
        
        Args:
            db: 数据库会话
            kwargs: 切片属性
                - user_id: 用户ID
                - document_id: 文档ID
                - task_id: 事项ID
                - content: 切片内容
                - vector: 文本向量
                - path: 文档路径
                - metadata_: 元数据
                - status: 状态
        
        Returns:
            创建的RagChunks对象
        """
        # 生成UUID作为ID
        if "id" not in kwargs:
            kwargs["id"] = str(uuid.uuid4())
        
        chunk = cls(**kwargs)
        db.add(chunk)
        # 不在这里commit，由外部统一管理事务
        return chunk
    
    @classmethod
    def bulk_create_chunks(cls, db: Session, chunks_data: List[Dict[str, Any]]) -> List["RagChunks"]:
        """
        批量创建文档切片
        
        Args:
            db: 数据库会话
            chunks_data: 切片数据列表
        
        Returns:
            创建的RagChunks对象列表
        """
        chunks = []
        for chunk_data in chunks_data:
            if "id" not in chunk_data:
                chunk_data["id"] = str(uuid.uuid4())
            chunks.append(cls(**chunk_data))
        
        db.add_all(chunks)
        # 不在这里commit，由外部统一管理事务
        return chunks
    
    @classmethod
    def get_chunks_by_document_id(cls, db: Session, document_id: str, user_id: Optional[int] = None) -> List["RagChunks"]:
        """
        根据文档ID获取所有切片
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            user_id: 可选，用户ID，用于权限控制
        
        Returns:
            切片对象列表
        """
        query = db.query(cls).filter(cls.document_id == document_id)
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.all()
    
    @classmethod
    def search_similar_chunks(cls, db: Session, query_vector: List[float], user_id: int, limit: int = 5, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        搜索相似的文档切片
        
        Args:
            db: 数据库会话
            query_vector: 查询向量
            user_id: 用户ID，用于权限控制
            limit: 返回结果数量
            threshold: 相似度阈值
        
        Returns:
            相似切片列表，包含相似度分数
        """
        # 使用pgvector的向量相似度查询
        results = db.query(
            cls
        ).add_columns(
            cls.vector.l2_distance(query_vector).label("distance")
        ).filter(
            cls.user_id == user_id
        ).order_by(
            "distance"
        ).limit(limit).all()
        
        # 转换为字典列表，包含相似度分数
        return [
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "path": chunk.path,
                "metadata": chunk.metadata_,
                "similarity": 1 / (1 + distance)  # 将距离转换为相似度分数(0-1)
            }
            for chunk, distance in results
            if 1 / (1 + distance) >= threshold
        ]
    
    @classmethod
    def search_similar_chunks_for_task(cls, db: Session, query_vector: List[float],  task_id: int, limit: int = 5, threshold: float = 0.01) -> List[Dict[str, Any]]:
        """
        搜索相似的文档切片
        
        Args:
            db: 数据库会话
            query_vector: 查询向量
            task_id: 事项ID，用于过滤
            limit: 返回结果数量
            threshold: 相似度阈值
        
        Returns:
            相似切片列表，包含相似度分数
        """
        # 使用pgvector的向量相似度查询
        results = db.query(
            cls
        ).add_columns(
            cls.vector.l2_distance(query_vector).label("distance")
        ).filter(
            cls.task_id == task_id
        ).order_by(
            "distance"
        ).limit(limit).all()
        
        # 转换为字典列表，包含相似度分数
        return [
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "path": chunk.path,
                "metadata": chunk.metadata_,
                "similarity": 1 / (1 + distance)  # 将距离转换为相似度分数(0-1)
            }
            for chunk, distance in results
            if 1 / (1 + distance) >= threshold
        ]

    @classmethod
    def delete_chunks_by_document_id(cls, db: Session, document_id: str, user_id: Optional[int] = None) -> int:
        """
        根据文档ID删除所有切片
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            user_id: 可选，用户ID，用于权限控制
        
        Returns:
            删除的切片数量
        """
        query = db.query(cls).filter(cls.document_id == document_id)
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        
        deleted_count = query.delete()
        db.commit()
        return deleted_count
    
    @classmethod
    def get_chunk_by_id(cls, db: Session, chunk_id: str, user_id: Optional[int] = None) -> Optional["RagChunks"]:
        """
        根据ID获取单个切片
        
        Args:
            db: 数据库会话
            chunk_id: 切片ID
            user_id: 可选，用户ID，用于权限控制
        
        Returns:
            RagChunks对象或None
        """
        query = db.query(cls).filter(cls.id == chunk_id)
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.first()
    
    def update(self, db: Session, **kwargs) -> "RagChunks":
        """
        更新切片信息
        
        Args:
            db: 数据库会话
            kwargs: 要更新的属性
        
        Returns:
            更新后的RagChunks对象
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        db.commit()
        db.refresh(self)
        return self
