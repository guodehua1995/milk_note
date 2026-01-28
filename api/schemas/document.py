from .base import BaseResponse
from typing import List, Optional

class DocumentResponse(BaseResponse):
    """
    文档响应模型。
    """
    document_id: str
    document_name: str
    document_status: str
    document_type: str
    created_at: str
    updated_at: str

class DocumentListResponse(BaseResponse):
    """
    文档列表响应模型。
    """
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int

class DocumentStatusResponse(BaseResponse):
    """
    文档状态响应模型。
    """
    document_id: str
    status: str
    progress: Optional[int] = 0
    message: Optional[str] = None

class UploadDocumentResponse(BaseResponse):
    """
    上传文档响应模型。
    """
    document_id: str
    message: str
    object_name: str

class DeleteDocumentResponse(BaseResponse):
    """
    删除文档响应模型。
    """
    document_id: str
    message: str