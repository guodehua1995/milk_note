from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader,Docx2txtLoader,TextLoader,UnstructuredMarkdownLoader,UnstructuredPDFLoader
from sqlalchemy.orm import Session
from langchain_core.documents import Document
from typing import List
import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from api.core import utils
from .vector import get_embedding

class VectorWriter:
    
    @classmethod
    def split_content(cls,file_url:str):
        """
            读取文件,切片并向量化存储
            支持跨平台(Windows/Linux)和带查询参数的URL
        """
        
        try:
            # 下载文件并保存到本地临时目录
            temp_file_path = utils.create_temp_file(file_url)
            # 加载文档
            documents = cls.__load_document(temp_file_path)
            document_content = "\n".join([doc.page_content for doc in documents])
            # 清洗 去空格等
            document_content = cls.__clean_document(document_content)
            # 切片文档
            chunks:List[str] = cls.__slice_document(document_content)   
            
            # 注意：这里应该添加清理临时文件的逻辑，避免磁盘占用
            os.unlink(temp_file_path)
            return chunks
        except Exception as e:
            print(f"文件处理失败：{e}")
            # 确保异常情况下临时文件也能被删除
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise
    
    @classmethod
    def vectorize(cls,content:str)->bytes:
        """
            向量化存储
        """
        return get_embedding(content)

    

    def __load_document(self,file_path:str):
        """
            加载文档
        """
        # 获取文件后缀名
        file_ext = Path(file_path).suffix.lower()
        print(file_ext)
        documents:List[Document] = []
        loader = None
        if file_ext == ".pdf":
            loader = PyPDFLoader(file_path,mode="single")
        elif file_ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif file_ext == ".txt":
            loader = TextLoader(file_path)
        elif file_ext == ".md":
            loader = UnstructuredMarkdownLoader(file_path)
        documents = loader.load()
        return documents

    def __clean_document(self,document_content:str):
        """
            清洗文档
        """
        # 清洗文档内容
        text = document_content.strip()
        text = re.sub(r"<\|", "<", text)
        text = re.sub(r"\|>", ">", text)
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]", "", text)
        # Unicode  U+FFFE
        text = re.sub("\ufffe", "", text)
        return text
    
    def __slice_document(self,document_content:str)->List[str]:
        """
            切片文档
        """
        # 切片文档
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ".","！","？","！？","。"],
            chunk_size=2000,
            chunk_overlap=100,
        )
        return text_splitter.split_text(document_content)

