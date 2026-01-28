import pytest
from unittest.mock import patch, MagicMock
from api.services.rag.vector import get_embedding
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 测试成功场景
@patch('api.services.rag.vector.settings')
def test_get_embedding_success(mock_settings):
    """测试成功获取文本向量"""
    # 配置 mock
    mock_settings.BAILIAN_AGENT_API_KEY = "sk-7ccbaad864134f7594de1426a9d1317d"
    mock_settings.BAILIAN_WORKSPACE_ID = "llm-u4vtkdq0nqf41iqc"
    
    # 调用要测试的函数
    text = "测试文本"
    result = get_embedding(text)
    print(f"获取到的文本向量：{result}")
