
from api.core import settings,VECTOR_DIMENSION
import dashscope
from typing import List
from http import HTTPStatus

def get_embedding(text:str)->List[float]:
    """
        获取文本向量
        返回1536维浮点数列表
    """
    resp = dashscope.TextEmbedding.call(
        model="text-embedding-v4",
        input=text,
        api_key=settings.BAILIAN_AGENT_API_KEY,
        workspace=settings.BAILIAN_WORKSPACE_ID,
        dimension=VECTOR_DIMENSION
    )
    if resp.status_code == HTTPStatus.OK:
        # 提取向量数据：resp.output结构为 {"embeddings": [{"embedding": [...], "text_index": 0}]}
        embeddings = resp.output.get('embeddings', [])
        if embeddings and len(embeddings) > 0:
            return embeddings[0]['embedding']  # 返回1536维向量列表 
        else:
            raise Exception("获取文本向量失败：响应中无embeddings数据")
    else:
        raise Exception(f"获取文本向量失败：{resp}")