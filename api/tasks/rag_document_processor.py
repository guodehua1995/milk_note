from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from api.core import get_db,oss_client,get_logger,DocumentStatus,ChunkStatus
from api.models.rag_models import RagDocument, RagChunks
from api.services.rag.writer import VectorWriter


logger = get_logger(__name__)
class RagDocumentProcessor:
    """
    RAG文档处理器，用于定时处理状态为pending的RagDocument
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        """
        启动处理器
        """
        # 添加定时任务，每10分钟执行一次
        self.scheduler.add_job(
            self.process_pending_documents,
            trigger=IntervalTrigger(minutes=1),
            id="process_pending_documents",
            name="处理状态为pending的RagDocument",
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.process_embdding_documents,
            trigger=IntervalTrigger(minutes=1),
            id="process_embdding_documents",
            name="处理状态为Embdding的document",
            replace_existing=True
        )
        # 立即执行一次，用于测试
        # self.scheduler.add_job(
        #     self.process_pending_documents,
        #     trigger="date",
        #     run_date=time.time() + 5,
        #     id="process_pending_documents_immediate",
        #     name="立即处理状态为pending的RagDocument",
        #     replace_existing=True
        # )
        
        # 启动调度器
        self.scheduler.start()
        logger.info("RAG文档处理器已启动")
    
    def shutdown(self):
        """
        关闭处理器
        """
        self.scheduler.shutdown()
        logger.info("RAG文档处理器已关闭")
    
    def process_pending_documents(self):
        """
        处理状态为pending的RagDocument
        """
        logger.debug("开始处理状态为pending的RagDocument...")
        
        try:
            # 查询所有状态为pending的RagDocument
            with next(get_db()) as db:
                pending_docs = db.query(RagDocument).filter(RagDocument.status == "pending").all()
            
            # logger.info(f"找到 {len(pending_docs)} 个状态为pending的RagDocument")
            
            if not pending_docs:
                return
            
            # 创建VectorWriter实例
           
            
            # 遍历处理每个文档
            for doc in pending_docs:

                logger.info(f"处理文档: {doc.file_name} (ID: {doc.id})")
                with next(get_db()) as db:
                    try:
                        # 获取文件URL（这里需要根据实际情况调整，将file_key转换为完整URL）
                        # 假设file_key已经是完整URL，或者需要拼接base_url
                        file_url = oss_client.path_for_download(doc.file_key)
                
                        # 调用VectorWriter进行文本切割
                        chunks = VectorWriter.split_content(file_url)
                        
                        logger.debug(f"文档切割完成，生成 {len(chunks)} 个chunk")
                        
                        # 生成RagChunks
                        chunks_data = []
                        for i, chunk_content in enumerate(chunks):
                            chunks_data.append({
                                "user_id": doc.user_id,
                                "document_id": doc.id,
                                "task_id": doc.task_id,
                                "content": chunk_content,
                                "vector": None,  # 暂时为空，后续可以添加向量生成逻辑
                                "path": doc.file_key,
                                "metadata_": {
                                    "chunk_index": i,
                                    "total_chunks": len(chunks),
                                    "document_name": doc.file_name,
                                    "document_type": doc.type
                                },
                                "status": ChunkStatus.PENDING.value
                            })
                        
                        # 批量创建RagChunks
                        RagChunks.bulk_create_chunks(db, chunks_data)
                        
                        # 更新RagDocument状态为embedding
                        doc.status = DocumentStatus.EMBEDDING.value
                        
                        logger.debug(f"文档 {doc.file_name} 处理完成！")     
                    except Exception as e:
                        logger.error(f"处理文档 {doc.file_name} 失败: {str(e)}")
                        # 更新RagDocument状态为failed
                        doc.status = DocumentStatus.FAILED.value
                        continue
            logger.debug("所有pending状态的RagDocument处理完成！")
            
        except Exception as e:
            logger.error(f"处理pending文档时发生错误: {str(e)}")


    def process_embdding_documents(self):
        """处理状态为embedding的document"""
        logger.debug("开始处理状态为embedding的document...")
    
        # 单个Session处理所有文档（安全，因为顺序执行）
        with next(get_db()) as session:
            try:
                splited_docs = session.query(RagDocument).filter(
                    RagDocument.status == DocumentStatus.EMBEDDING.value
                ).all()
                
                # logger.debug(f"找到 {len(splited_docs)} 个状态为splited的RagDocument")
                
                if not splited_docs:
                    return
            
                for doc in splited_docs:
                    logger.debug(f"处理文档: {doc.file_name} (ID: {doc.id})")
                    
                    try:
                        # 1. 查询当前文档的待处理chunk
                        pending_chunks = session.query(RagChunks).filter(
                            RagChunks.document_id == doc.id,
                            RagChunks.status == ChunkStatus.PENDING.value
                        ).all()
                        
                        if not pending_chunks:
                            # 没有待处理chunk，直接标记为completed
                            doc.status = DocumentStatus.COMPLETED.value
                            session.commit()
                            continue
                            
                        # 3. 处理每个chunk
                        all_ok = True
                        for chunk in pending_chunks:
                            try:
                                logger.debug(f"处理chunk: {chunk.content[:50]}...")
                                # 向量化处理
                                vector_data = VectorWriter.vectorize(chunk.content)
                                # 更新chunk状态
                                chunk.vector = vector_data
                                chunk.status = ChunkStatus.COMPLETED.value
                                logger.debug(f"chunk处理完成！")
                            except Exception as e:
                                logger.error(f"处理chunk失败: {str(e)}")
                                chunk.status = ChunkStatus.FAILED.value
                                all_ok = False
                                break  # 一个chunk失败，终止当前文档处理
                        
                        # 4. 根据处理结果更新文档状态
                        if all_ok:
                            doc.status = DocumentStatus.COMPLETED.value
                            logger.info(f"文档 {doc.file_name} 所有chunk处理完成！")
                        else:
                            doc.status = DocumentStatus.FAILED.value
                            logger.error(f"文档 {doc.file_name} 处理失败！")
                        
                        # 5. 提交当前文档的所有变更
                        session.commit()
                        
                    except Exception as e:
                        logger.error(f"处理文档 {doc.file_name} 失败: {str(e)}")
                        # 单独提交失败状态
                        doc.status = DocumentStatus.FAILED.value
                        session.commit()
                        
            except Exception as e:
                logger.error(f"处理chunks时发生错误: {str(e)}")
                session.rollback()

# 创建处理器实例
rag_document_processor = RagDocumentProcessor()
