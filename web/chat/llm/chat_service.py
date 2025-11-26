from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

import os
import logging

# 配置日志
logger = logging.getLogger(__name__)

class LangChainChatService:
    """LangChain聊天服务，集成数据库存储和LLM"""
    
    def __init__(self):
        # 初始化LLM
        api_key = os.environ.get("MILK_NOTE_API_KEY")
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            temperature=0.7
        )
        
        # 创建提示模板，包含系统消息、历史消息和用户问题
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="你是一个有帮助的个人助理。请根据用户的提问和对话历史提供有用的回答。"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}")
        ])
        
        # 创建链
        self.chain = self.prompt | self.llm
    
    def get_chat_history(self, user_id, conversation_id=None):
        """获取用户的聊天历史"""
        from chat.services.memory_manager import MemoryManager
        memory_manager = MemoryManager(user_id)
        return memory_manager.get_short_term_memory(conversation_id)
    
    def get_chain_with_history(self):
        """创建带有历史记录的链"""
        def get_session_history(user_id, conversation_id=None):
            """获取会话历史"""
            from chat.services.memory_manager import MemoryManager
            memory_manager = MemoryManager(user_id)
            return memory_manager.get_short_term_memory(conversation_id)
        
        return RunnableWithMessageHistory(
            self.chain,
            lambda user_id, conversation_id: get_session_history(user_id, conversation_id),
            input_messages_key="input",
            history_messages_key="chat_history"
        )
    
    def chat(self, user_id, input_text, conversation_id=None, metadata=None, stream=False, system_prompt=None):
        """处理聊天请求，支持流式输出
        
        Args:
            user_id: 用户ID
            input_text: 用户输入文本
            conversation_id: 会话ID
            metadata: 元数据
            stream: 是否启用流式输出，默认为False
            system_prompt: 额外的系统提示词（如事项长期记忆）
            
        Returns:
            如果stream=False，返回dict: 包含回复和会话信息的字典
            如果stream=True，返回生成器: 逐个产生响应片段
        """
        # 获取长期记忆，添加到系统消息中
        from chat.services.memory_manager import MemoryManager
        memory_manager = MemoryManager(user_id)
        long_term_memory = memory_manager.get_long_term_memory()
        
        logger.info(f"获取到长期记忆: {long_term_memory}")
        
        # 更新系统提示，包含用户的长期记忆
        base_system_prompt = self._generate_personalized_system_prompt(long_term_memory)
        
        # 如果有额外的系统提示词（如事项长期记忆），合并到系统提示中
        if system_prompt:
            base_system_prompt += f"\n\n以下是当前事项的长期记忆：\n{system_prompt}"
        
        # 创建个性化的链
        personalized_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=base_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}")
        ])
        personalized_chain = personalized_prompt | self.llm
        
        # 获取带有历史记录的链
        chain_with_history = RunnableWithMessageHistory(
            personalized_chain,
            lambda: memory_manager.get_short_term_memory(conversation_id),
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        
        # 获取会话ID
        conversation = memory_manager.get_short_term_memory(conversation_id)
        
        # 如果是第一条消息，可以生成会话标题
        if conversation_id is None and input_text:
            # 这里可以使用LLM生成标题
            # title = self._generate_conversation_title(input_text, response.content)
            # conversation.update_conversation_title(title)
            pass
        
        conversation_id_result = conversation.get_conversation_id()
        
        # 非流式输出
        if not stream:
            response = chain_with_history.invoke(
                {"input": input_text},
                config={"configurable": {"session_id": str(conversation_id or "default")}}
            )
            # 确保所有字段都是可序列化的
            response_content = response.content if hasattr(response, 'content') else str(response)
            conversation_id_str = str(conversation_id_result) if conversation_id_result else None
            metadata_dict = metadata if isinstance(metadata, dict) else {}
            
            return {
                "response": response_content,
                "conversation_id": conversation_id_str,
                "metadata": metadata_dict
            }
        
        # 流式输出 - 返回生成器
        def stream_generator():
            # 使用stream方法获取流式响应
            stream_response = chain_with_history.stream(
                {"input": input_text},
                config={"configurable": {"session_id": str(conversation_id or "default")}}
            )
            
            full_response = ""
            # 逐个生成响应片段
            for chunk in stream_response:
                if hasattr(chunk, 'content'):
                    chunk_content = chunk.content
                    full_response += chunk_content
                    yield {
                        "chunk": chunk_content,
                        "conversation_id": str(conversation_id_result),  # 确保是字符串
                        "metadata": metadata if metadata is not None else {},  # 确保是字典
                        "is_complete": False
                    }
            
            # 生成最后一个完整的响应
            yield {
                "chunk": "",  # 空内容表示结束
                "conversation_id": str(conversation_id_result),  # 确保是字符串
                "metadata": metadata if metadata is not None else {},  # 确保是字典
                "is_complete": True,
                "full_response": full_response
            }
        
        return stream_generator()
    
    def _generate_personalized_system_prompt(self, long_term_memory):
        """生成个性化的系统提示词"""

        base_prompt = "你是一个有帮助的个人助理。请根据用户的提问和对话历史提供有用的回答。"
        
        if long_term_memory.get("name"):
            base_prompt += f"\n用户的名字是{long_term_memory['name']}。"
        
        if long_term_memory.get("assistant_name"):
            base_prompt += f"\n你的名字是{long_term_memory['assistant_name']}。"

        if long_term_memory.get("key_points"):
            base_prompt += f"\n以下是关于用户的重要信息：{long_term_memory['key_points']}"
        
        if long_term_memory.get("style_prompt"):
            base_prompt += f"\n请以{long_term_memory['style_prompt']}的风格回答,注意:重点是回答用户问题而不是模仿人设,禁止因模仿人设而添加过多的元素导致对话出现不真实感。"
        
        logger.info(f"生成的系统提示词: {base_prompt}")
        return base_prompt
    
    def _generate_conversation_title(self, user_input, ai_response):
        """生成会话标题"""
        # 简化实现，实际应使用LLM生成
        return user_input[:50] if user_input else "新对话"