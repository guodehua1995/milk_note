
from fastapi import HTTPException
from api.core import get_logger
from api.models import RagDocument, RagChunks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from datetime import datetime
from .rag import get_embedding

logger = get_logger(__name__)

class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def insert_document(self, user_id: str, task_id: str, file_name: str, file_key: str) -> RagDocument:
        """
        插入文档到知识库索引。

        参数:
            user_id (str): 用户ID。
            task_id (str): 事项ID。
            file_name (str): 文件名。
            file_key (str): 文件在OSS中的路径。
        
        返回:
            RagDocument: 创建的文档对象。
        """
        # 创建文档
        rag_document = RagDocument(
            user_id=user_id,
            task_id=task_id,
            type=file_name.split(".")[-1],
            file_name=file_name,
            file_key=file_key,
        )
        self.db.add(rag_document)
        self.db.commit()
        self.db.refresh(rag_document)
        
        return rag_document

    def get_document_by_id(self, document_id: str, user_id: str) -> Optional[RagDocument]:
        """
        根据文档ID获取文档信息。

        参数:
            document_id (str): 文档ID。
            user_id (str): 用户ID，用于权限验证。
        
        返回:
            Optional[RagDocument]: 文档对象或None。
        """
        return self.db.query(RagDocument).filter(
            and_(
                RagDocument.id == document_id,
                RagDocument.user_id == user_id,
                RagDocument.is_deleted == False
            )
        ).first()

    def get_document_status(self, document_id: str, user_id: str) -> Optional[dict]:
        """
        获取文档解析状态。

        参数:
            document_id (str): 文档ID。
            user_id (str): 用户ID，用于权限验证。
        
        返回:
            Optional[dict]: 包含状态和进度的字典。
        """
        document = self.get_document_by_id(document_id, user_id)
        if not document:
            return None
        
        return {
            "document_id": document.id,
            "status": document.status,
            "progress": 100 if document.status == "completed" else 0,
            "message": f"文档{document.status}"
        }

    def update_document_status(self, document_id: str, status: str) -> bool:
        """
        更新文档状态。

        参数:
            document_id (str): 文档ID。
            status (str): 新状态。
        
        返回:
            bool: 更新是否成功。
        """
        try:
            document = self.db.query(RagDocument).filter(RagDocument.id == document_id).first()
            if document:
                document.status = status
                document.updated_at = datetime.now()
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            return False

    def delete_document(self, document_id: str, user_id: str) -> bool:
        """
        删除文档（软删除）。

        参数:
            document_id (str): 文档ID。
            user_id (str): 用户ID，用于权限验证。
        
        返回:
            bool: 删除是否成功。
        """
        try:
            document = self.get_document_by_id(document_id, user_id)
            if document:
                document.is_deleted = True
                document.delete_at = datetime.now()
                document.status = "deleted"
                document.updated_at = datetime.now()
                
                # 级联删除相关的chunks会由SQLAlchemy自动处理
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            return False

    def get_user_documents(self, user_id: str, page: int = 1, page_size: int = 10, task_id: Optional[str] = None) -> dict:
        """
        获取用户的文档列表。

        参数:
            user_id (str): 用户ID。
            page (int): 页码，默认为1。
            page_size (int): 每页大小，默认为10。
            task_id (Optional[str]): 可选的事项ID，用于过滤。
        
        返回:
            dict: 包含文档列表、总数、页码和页大小的字典。
        """
        query = self.db.query(RagDocument).filter(
            and_(
                RagDocument.user_id == user_id,
                RagDocument.is_deleted == False
            )
        )
        
        # 如果提供了task_id，则过滤该事项下的文档
        if task_id:
            query = query.filter(RagDocument.task_id == task_id)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        documents = query.order_by(RagDocument.created_at.desc()).offset(offset).limit(page_size).all()
        
        return {
            "documents": documents,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def get_document_chunks(self, document_id: str, user_id: str) -> List[RagChunks]:
        """
        获取文档的所有切片。

        参数:
            document_id (str): 文档ID。
            user_id (str): 用户ID，用于权限验证。
        
        返回:
            List[RagChunks]: 切片列表。
        """
        document = self.get_document_by_id(document_id, user_id)
        if not document:
            return []
        
        return document.chunks

    def batch_delete_documents(self, document_ids: List[str], user_id: str) -> dict:
        """
        批量删除文档。

        参数:
            document_ids (List[str]): 文档ID列表。
            user_id (str): 用户ID，用于权限验证。
        
        返回:
            dict: 包含成功和失败的文档ID的字典。
        """
        success_ids = []
        failed_ids = []
        
        for doc_id in document_ids:
            if self.delete_document(doc_id, user_id):
                success_ids.append(doc_id)
            else:
                failed_ids.append(doc_id)
        
        return {
            "success_ids": success_ids,
            "failed_ids": failed_ids,
            "total_success": len(success_ids),
            "total_failed": len(failed_ids)
        }

    def search_similar_chunks_for_task(self, content: str, task_id: int, limit: int = 5, threshold: float = 0.8)->List[Dict[str, Any]]:
         # 将content转换为向量
        try:
            # logger.debug(f"正在为任务 {task_id} 搜索相似切片，查询内容: {content}, 阈值: {threshold}")
            query_vector = get_embedding(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return RagChunks.search_similar_chunks_for_task(self.db, query_vector, task_id, limit, threshold)

    def search_similar_chunks(self, content: str, user_id: str, limit: int = 5, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        搜索相似的文档切片。

        参数:
            query_vector (List[float]): 查询向量。
            user_id (str): 用户ID，用于权限验证。
            limit (int): 返回结果数量，默认为5。
            threshold (float): 相似度阈值，默认为0.8。
        
        返回:
            List[Dict[str, Any]]: 相似切片列表，包含相似度分数。
        """

        # 将content转换为向量
        try:
            query_vector = get_embedding(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return RagChunks.search_similar_chunks(self.db, query_vector, user_id, limit, threshold)

    def get_documents_by_task_id(self, task_id: int, user_id: str) -> Optional[List[RagDocument]]:
        """
        根据任务ID获取文档。

        参数:
            task_id (str): 任务ID。
            user_id (str): 用户ID，用于权限验证。
        
        返回:
            Optional[List[RagDocument]]: 文档对象列表，如果不存在则返回None。
        """
        return self.db.query(RagDocument).filter(
            and_(
                RagDocument.task_id == task_id,
                RagDocument.user_id == user_id,
                RagDocument.is_deleted == False
            )
        ).all()
    
    def bind_task_to_documents(self, task_id: int, document_ids: List[str], user_id: str) -> dict:
        """
        将任务绑定到文档。
        """
        for doc_id in document_ids:
            document = self.get_document_by_id(doc_id, user_id)
            if document:
                document.task_id = task_id
        self.db.commit()
        return {"message": "文档绑定成功"}
       


