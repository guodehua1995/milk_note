from chat.models import UserProfile, Conversation, ChatMessage
from chat.llm.database_chat_history import DatabaseChatMessageHistory
from datetime import datetime, timedelta
from django.utils import timezone

class MemoryManager:
    """记忆管理服务，处理短期和长期记忆"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self._ensure_user_profile()
    
    def _ensure_user_profile(self):
        """确保用户配置文件存在"""
        try:
            self.user_profile = UserProfile.objects.get(user_id=self.user_id)
        except UserProfile.DoesNotExist:
            self.user_profile = UserProfile.objects.create(user_id=self.user_id)
    
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
        return {
            "name": self.user_profile.name,
            "key_points": self.user_profile.key_points,
            "preferences": self.user_profile.preferences
        }
    
    def update_user_profile(self, name=None, key_points=None, preferences=None):
        """更新用户长期记忆"""
        if name is not None:
            self.user_profile.name = name
        if key_points is not None:
            self.user_profile.key_points = key_points
        if preferences is not None:
            self.user_profile.preferences = preferences
        
        self.user_profile.save()
    
    def get_user_conversations(self, limit=20, include_messages=False):
        """获取用户的所有会话
        
        Args:
            limit: 限制返回会话数量
            include_messages: 是否包含消息内容
            
        Returns:
            list: 会话列表
        """
        conversations = Conversation.objects.filter(
            user_id=self.user_id
        ).order_by('-updated_at')[:limit]
        
        result = []
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
            
            result.append(conv_data)
        
        return result
    
    def summarize_conversation(self, conversation_id):
        """将会话总结添加到长期记忆"""
        try:
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