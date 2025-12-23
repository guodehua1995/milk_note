from chat.models import UserChatProfile, ChatMessage
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
    
    def get_short_term_memory(self, issue_id=None):
        """获取短期记忆（当前事项的聊天历史）
        
        Args:
            issue_id: 事项ID，如果为None则表示无事项的聊天
            
        Returns:
            DatabaseChatMessageHistory: 数据库聊天历史实例
        """
        return DatabaseChatMessageHistory(self.user_id, issue_id)
    
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