from django.db import models
from django.conf import settings
from django.utils import timezone
import json

class Conversation(models.Model):
    """对话会话模型，用于管理用户的多个会话"""
    # 使用Django默认的User模型或自定义用户模型
    user_id = models.CharField(max_length=100, db_index=True, help_text="用户标识")
    title = models.CharField(max_length=200, default="新对话", help_text="会话标题")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="最后更新时间")
    is_active = models.BooleanField(default=True, help_text="是否激活")
    
    def __str__(self):
        return f"会话-{self.user_id}-{self.title[:20]}"

class ChatMessage(models.Model):
    """聊天消息模型，存储对话中的每条消息"""
    ROLE_CHOICES = [
        ('system', '系统'),
        ('user', '用户'),
        ('assistant', '助手'),
        ('tool', '工具'),
    ]
    
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE, help_text="所属会话")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, help_text="消息角色")
    content = models.TextField(help_text="消息内容")
    message_id = models.CharField(max_length=100, null=True, blank=True, help_text="消息唯一标识")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    metadata = models.JSONField(null=True, blank=True, help_text="额外元数据")
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}"

class UserProfile(models.Model):
    """用户配置文件，存储用户的长期记忆"""
    user_id = models.CharField(max_length=100, unique=True, db_index=True, help_text="用户标识")
    name = models.CharField(max_length=100, null=True, blank=True, help_text="用户名称")
    preferences = models.JSONField(default=dict, help_text="用户偏好设置")
    key_points = models.TextField(null=True, blank=True, help_text="记忆要点")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    def __str__(self):
        return f"用户-{self.user_id}"
