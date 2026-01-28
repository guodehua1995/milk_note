from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List, Optional
from api.models import User, Session
from api.core import get_current_active_user, oss_client, get_db
from fastapi import UploadFile, File
from api.services import DocumentService
from api.schemas import (
    DocumentResponse, DocumentListResponse, DocumentStatusResponse,
    UploadDocumentResponse, DeleteDocumentResponse, BaseResponse
)

router = APIRouter(prefix="/document", tags=["文档"])


@router.get("/search", response_model=BaseResponse)
def search_similar_chunks(
    content: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]):
    """
    搜索相似的文档切片
    - 需要用户认证
    - 返回相似切片列表，包含相似度分数
    - 用于调试和查看文档解析结果
    """
    document_service = DocumentService(db)
    chunks = document_service.search_similar_chunks(
        content,
        current_user.id,
        threshold=0.1
    )
    
    base_response = BaseResponse(
        data=chunks,
        message="搜索成功"
    )
    
    return base_response

@router.post("/upload", response_model=UploadDocumentResponse)
def upload_document(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
    task_id: Optional[str] = None):
    """
    上传文档到知识库
    - 需要用户认证
    - 支持多种文件类型（PDF、Word、TXT等）
    - 自动上传到OSS存储
    - 返回文档ID和状态
    """
    try:
        # 上传文件到OSS
        object_name = f"documents/{current_user.id}/{file.filename}"
        oss_client.upload_file(object_name, file.file.read())
        
        # 插入文档到知识库索引
        document_service = DocumentService(db)
        rag_document = document_service.insert_document(
            user_id=current_user.id,
            task_id=task_id,
            file_name=file.filename,
            file_key=object_name,
        )
        
        return UploadDocumentResponse(
            document_id=rag_document.id,
            message="文件上传成功",
            object_name=object_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/status/{document_id}", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]):
    """
    查询文档解析状态
    - 需要用户认证
    - 通过文档ID查询解析进度和状态
    - 返回状态、进度百分比和状态信息
    """
    document_service = DocumentService(db)
    status_info = document_service.get_document_status(document_id, current_user.id)
    
    if not status_info:
        raise HTTPException(status_code=404, detail="文档不存在或无权访问")
    
    return DocumentStatusResponse(**status_info)

@router.get("/list", response_model=DocumentListResponse)
def get_document_list(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    task_id: Optional[str] = Query(None, description="事项ID，可选过滤条件")):
    """
    获取用户文档列表
    - 需要用户认证
    - 支持分页查询
    - 支持按事项ID过滤
    - 返回文档列表、总数、页码和页大小
    """
    document_service = DocumentService(db)
    result = document_service.get_user_documents(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        task_id=task_id
    )
    
    # 转换为响应模型
    documents = []
    for doc in result["documents"]:
        documents.append(DocumentResponse(
            document_id=doc.id,
            document_name=doc.file_name,
            document_status=doc.status,
            document_type=doc.type,
            created_at=doc.created_at.isoformat(),
            updated_at=doc.updated_at.isoformat()
        ))
    
    return DocumentListResponse(
        documents=documents,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )

@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]):
    """
    删除单个文档
    - 需要用户认证
    - 软删除机制，保留数据库记录
    - 自动删除关联的文档切片
    """
    document_service = DocumentService(db)
    success = document_service.delete_document(document_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在或无权访问")
    
    return DeleteDocumentResponse(
        document_id=document_id,
        message="文档删除成功"
    )

@router.delete("/batch/delete", response_model=DeleteDocumentResponse)
def batch_delete_documents(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    document_ids: List[str] = Query(..., description="文档ID列表")):
    """
    批量删除文档
    - 需要用户认证
    - 支持同时删除多个文档
    - 软删除机制
    - 返回删除结果
    """
    document_service = DocumentService(db)
    result = document_service.batch_delete_documents(document_ids, current_user.id)
    
    if result["total_success"] == 0:
        raise HTTPException(status_code=404, detail="所有文档删除失败或无权访问")
    
    return DeleteDocumentResponse(
        document_id=f"{result['total_success']}个文档",
        message=f"成功删除{result['total_success']}个文档，失败{result['total_failed']}个"
    )

@router.get("/{document_id}/chunks", response_model=dict)
def get_document_chunks(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]):
    """
    获取文档的所有切片
    - 需要用户认证
    - 返回文档的所有文本切片和向量信息
    - 用于调试和查看文档解析结果
    """
    document_service = DocumentService(db)
    chunks = document_service.get_document_chunks(document_id, current_user.id)
    
    if not chunks:
        raise HTTPException(status_code=404, detail="文档不存在或无权访问")
    
    # 转换为响应格式
    chunks_response = []
    for chunk in chunks:
        chunks_response.append({
            "chunk_id": chunk.id,
            "content": chunk.content,
            "metadata": chunk.metadata,
            "created_at": chunk.created_at.isoformat()
        })
    
    return {
        "document_id": document_id,
        "chunks_count": len(chunks_response),
        "chunks": chunks_response
    }
