from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
import os

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
    
    def chat(self, user_id, input_text, conversation_id=None, metadata=None):
        """处理聊天请求
        
        Args:
            user_id: 用户ID
            input_text: 用户输入文本
            conversation_id: 会话ID
            metadata: 元数据
            
        Returns:
            dict: 包含回复和会话信息的字典
        """
        # 获取长期记忆，添加到系统消息中
        from chat.services.memory_manager import MemoryManager
        memory_manager = MemoryManager(user_id)
        long_term_memory = memory_manager.get_long_term_memory()
        
        # 更新系统提示，包含用户的长期记忆
        system_prompt = self._generate_personalized_system_prompt(long_term_memory)
        
        # 创建个性化的链
        personalized_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
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
        
        # 调用链获取回复
        response = chain_with_history.invoke(
            {"input": input_text},
            config={"configurable": {"session_id": str(conversation_id or "default")}}
        )
        
        # 获取会话ID
        conversation = memory_manager.get_short_term_memory(conversation_id)
        
        # 如果是第一条消息，可以生成会话标题
        if conversation_id is None and input_text:
            # 这里可以使用LLM生成标题
            # title = self._generate_conversation_title(input_text, response.content)
            # conversation.update_conversation_title(title)
            pass
        
        return {
            "response": response.content,
            "conversation_id": conversation.get_conversation_id(),
            "metadata": metadata
        }
    
    def _generate_personalized_system_prompt(self, long_term_memory):
        """生成个性化的系统提示词"""
        base_prompt = "你是一个有帮助的个人助理。请根据用户的提问和对话历史提供有用的回答。"
        
        if long_term_memory.get("name"):
            base_prompt += f"\n用户的名字是{long_term_memory['name']}。"
        
        if long_term_memory.get("key_points"):
            base_prompt += f"\n以下是关于用户的重要信息：{long_term_memory['key_points']}"
        
        if long_term_memory.get("preferences"):
            base_prompt += f"\n用户的偏好设置：{str(long_term_memory['preferences'])}"
        
        return base_prompt
    
    def _generate_conversation_title(self, user_input, ai_response):
        """生成会话标题"""
        # 简化实现，实际应使用LLM生成
        return user_input[:50] if user_input else "新对话"