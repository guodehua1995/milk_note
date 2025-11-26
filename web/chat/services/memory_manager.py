from chat.models import UserChatProfile, Conversation, ChatMessage
from chat.llm.database_chat_history import DatabaseChatMessageHistory
from datetime import datetime, timedelta
from django.utils import timezone
import json
import logging
from ..llm.prompts import get_prompt_by_style

# 配置日志
logger = logging.getLogger(__name__)

class MemoryManager:
    """记忆管理服务，处理短期和长期记忆"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self._ensure_user_profile()
    
    def _ensure_user_profile(self):
        """确保用户配置文件存在"""
        try:
            # 使用正确的外键查询语法
            self.user_profile = UserChatProfile.objects.get(user_id=self.user_id)
        except UserChatProfile.DoesNotExist:
            # 创建新的用户配置文件
            self.user_profile = UserChatProfile.objects.create(user_id=self.user_id)
    
    def get_short_term_memory(self, conversation_id=None):
        """获取短期记忆（当前会话）
        
        Args:
            conversation_id: 会话ID，如果为None则创建新会话
            
        Returns:
            DatabaseChatMessageHistory: 数据库聊天历史实例
        """
        return DatabaseChatMessageHistory(self.user_id, conversation_id)
    
    def get_long_term_memory(self):
        """获取长期记忆（用户资料和关键信息）"""
        logger.info(f"开始获取用户 {self.user_id} 的长期记忆")
        logger.info(f"用户风格: {self.user_profile.style}")
        logger.info(f"助手名称: {self.user_profile.assistant_name}")
        logger.info(f"注意事项: {self.user_profile.extra_notice}")
        
        style_prompt = get_prompt_by_style(self.user_profile.style)
        logger.info(f"获取到的风格提示词: {style_prompt}")
        
        result = {
            "name": self.user_profile.name,
            "key_points": self.user_profile.key_points,
            "style_prompt": style_prompt,
            "assistant_name": self.user_profile.assistant_name,
            "extra_notice": self.user_profile.extra_notice
        }
        
        logger.info(f"返回的长期记忆: {result}")
        return result
    
    def update_user_profile(self, name=None, key_points=None, style=None, assistant_name=None, extra_notice=None):
        """更新用户长期记忆"""
        if name is not None:
            self.user_profile.name = name
        if key_points is not None:
            self.user_profile.key_points = key_points
        if style is not None:
            self.user_profile.style = style
        if assistant_name is not None:
            self.user_profile.assistant_name = assistant_name
        if extra_notice is not None:
            self.user_profile.extra_notice = extra_notice
        
        self.user_profile.save()
    
    def get_user_conversations(self, limit=20, include_messages=False, page=1, page_size=None):
        """获取用户的所有会话，支持分页查询
        
        Args:
            limit: 限制返回会话数量（已弃用，建议使用page_size）
            include_messages: 是否包含消息内容
            page: 页码，默认为1
            page_size: 每页大小，如果为None则使用limit值
            
        Returns:
            dict: 包含分页信息和会话列表的字典
        """
        # 使用page_size，如果未提供则使用limit
        if page_size is None:
            page_size = limit
            
        # 确保页码至少为1
        page = max(1, page)
        
        # 获取查询集（不立即执行），使用正确的外键查询语法
        queryset = Conversation.objects.filter(user_id=self.user_id)
        
        # 获取总数
        total_count = queryset.count()
        
        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取当前页的数据
        conversations = queryset.order_by('-updated_at')[offset:offset + page_size]
        
        # 处理数据
        items = []
        for conv in conversations:
            conv_data = {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "is_active": conv.is_active
            }
            
            if include_messages:
                messages = ChatMessage.objects.filter(conversation=conv)
                conv_data["messages"] = [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at
                    } for msg in messages
                ]
            
            items.append(conv_data)
        
        # 返回包含分页信息的结果
        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    def summarize_conversation(self, conversation_id):
        """将会话总结添加到长期记忆"""
        try:
            # 使用正确的外键查询语法
            conversation = Conversation.objects.get(id=conversation_id, user_id=self.user_id)
            
            # 获取会话中的最近消息（如最近10条）
            recent_messages = ChatMessage.objects.filter(
                conversation=conversation
            ).order_by('-created_at')[:10]
            
            # 这里可以调用LLM生成总结
            # 例如：summary = llm.generate_summary([msg.content for msg in reversed(recent_messages)])
            
            # 简化实现，实际应该使用LLM生成总结
            # summary = f"对话总结：{recent_messages[0].content[:100]}..."
            
            # 更新用户的关键记忆点
            # self.update_user_profile(key_points=summary)
            
            return True
        except Conversation.DoesNotExist:
            return False