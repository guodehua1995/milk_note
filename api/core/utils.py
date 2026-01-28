import os
import tempfile
import requests
import urllib.parse
from pathlib import Path

def create_temp_file(file_url:str) -> str:
    """
        创建临时文件
        
        Args:
            file_url (str): 文件URL。
        
        Returns:
            str: 临时文件路径。
    """
    try:
        # 解析URL，获取文件名和后缀
        parsed_url = urllib.parse.urlparse(file_url)
        # 从路径中提取文件名，处理查询参数
        path = parsed_url.path
        file_name = os.path.basename(path)  # 获取最后一个斜杠后的内容
        # 提取文件后缀
        file_suffix = Path(file_name).suffix

        # 使用tempfile.NamedTemporaryFile创建临时文件，suffix参数确保正确的文件后缀
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_file:
            # 使用requests下载文件内容
            response = requests.get(file_url, stream=True)  # 使用stream=True处理大文件
            response.raise_for_status()  # 检查HTTP响应状态
            # 分块写入文件，避免占用过多内存
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file_path = temp_file.name
    except Exception as e:
        print(f"文件处理失败：{e}")
        # 确保异常情况下临时文件也能被删除
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise Exception(f"文件处理失败：{e}")
    return temp_file_path