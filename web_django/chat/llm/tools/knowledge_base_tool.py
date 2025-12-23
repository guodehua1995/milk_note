from typing import List, Dict, Any
from langchain_core.tools import tool
from chat.models import KnowledgeBase, KnowledgeDocument
from django.db.models import Q


@tool
def search_knowledge_base(query: str, issue_id: int) -> List[Dict[str, Any]]:
    """
    搜索事项的知识库，返回相关的文档信息。
    
    Args:
        query: 搜索查询字符串
        issue_id: 事项ID，用于指定要搜索的知识库
        
    Returns:
        List[Dict[str, Any]]: 搜索结果列表，每个结果包含文档ID、标题和内容摘要
    """
    try:
        # 获取事项的知识库
        knowledge_base = KnowledgeBase.objects.get(issue_id=issue_id)
        
        # 在知识库的文档中搜索相关内容
        # 使用Q对象进行标题和内容的模糊搜索
        results = KnowledgeDocument.objects.filter(
            Q(knowledge_base=knowledge_base) & 
            (Q(title__icontains=query) | Q(content__icontains=query))
        )[:10]  # 最多返回10个结果
        
        # 构建搜索结果
        search_results = []
        for doc in results:
            # 生成内容摘要，截取前200个字符
            content_summary = doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            
            search_results.append({
                "document_id": doc.id,
                "title": doc.title,
                "content_summary": content_summary,
                "file_name": doc.file_name,
                "created_at": doc.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return search_results
    except KnowledgeBase.DoesNotExist:
        return [{"error": "知识库不存在"}]
    except Exception as e:
        return [{"error": f"搜索失败: {str(e)}"}]


@tool
def get_document_content(document_id: int) -> Dict[str, Any]:
    """
    获取指定文档的完整内容。
    
    Args:
        document_id: 文档ID
        
    Returns:
        Dict[str, Any]: 文档完整内容
    """
    try:
        # 获取文档
        doc = KnowledgeDocument.objects.get(id=document_id)
        
        return {
            "document_id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "file_name": doc.file_name,
            "created_at": doc.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    except KnowledgeDocument.DoesNotExist:
        return {"error": "文档不存在"}
    except Exception as e:
        return {"error": f"获取文档失败: {str(e)}"}