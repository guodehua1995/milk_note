from django.db import models
from django.conf import settings
from django.utils import timezone
import json
# 使用我们自定义的User模型
from login.models import User

class Issue(models.Model):
    """事项模型，用于管理用户的事项"""
    STATUS_CHOICES = [
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    # 使用自定义User模型，设置null=True以兼容现有数据
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issues', help_text="关联用户")
    title = models.CharField(max_length=200, help_text="事项标题")
    description = models.TextField(blank=True, null=True, help_text="事项描述")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', help_text="事项状态")
    long_term_memory = models.TextField(blank=True, null=True, help_text="长期记忆，格式：时间:事件描述;时间:事件描述;")
    last_memory_update = models.DateTimeField(auto_now_add=True, help_text="最后记忆更新时间")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="最后更新时间")
    
    def __str__(self):
        return f"事项-{self.user.username if hasattr(self.user, 'username') else self.user.id}-{self.title[:20]}"

class ChatMessage(models.Model):
    """聊天消息模型，存储对话中的每条消息"""
    ROLE_CHOICES = [
        ('system', '系统'),
        ('user', '用户'),
        ('assistant', '助手'),
        ('tool', '工具'),
    ]
    
    # 直接关联用户和事项，去掉会话概念
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='chat_messages', help_text="关联用户")
    issue = models.ForeignKey(Issue, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_messages', help_text="关联事项")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, help_text="消息角色")
    content = models.TextField(help_text="消息内容")
    message_id = models.CharField(max_length=100, null=True, blank=True, help_text="消息唯一标识")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    metadata = models.JSONField(null=True, blank=True, help_text="额外元数据")
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}"

class UserChatProfile(models.Model):
    """用户聊天配置文件，存储用户的长期记忆"""
    # 使用自定义User模型关联，设置null=True以兼容现有数据
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, related_name='chat_profile', help_text="关联用户")
    name = models.CharField(max_length=100, null=True, blank=True, help_text="用户名称")
    style = models.CharField(max_length=20, default='general', help_text="聊天风格")
    assistant_name = models.CharField(max_length=10, default='助手', help_text="助手名称")
    extra_notice = models.CharField(max_length=200, blank=True, null=True, help_text="注意事项")
    key_points = models.TextField(null=True, blank=True, help_text="记忆要点")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    def __str__(self):
        return f"用户-{self.user.username if hasattr(self.user, 'username') else self.user.id}"


class KnowledgeBase(models.Model):
    """知识库模型，每个事项对应一个专属知识库"""
    # 与事项一一关联
    issue = models.OneToOneField(Issue, on_delete=models.CASCADE, related_name='knowledge_base', help_text="关联事项")
    name = models.CharField(max_length=200, help_text="知识库名称")
    description = models.TextField(blank=True, null=True, help_text="知识库描述")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    def __str__(self):
        return f"知识库-{self.issue.title[:20]}"


class KnowledgeDocument(models.Model):
    """知识库文档模型，存储知识库中的文档"""
    # 与知识库关联
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='documents', help_text="关联知识库")
    title = models.CharField(max_length=200, help_text="文档标题")
    content = models.TextField(help_text="文档内容")
    file_name = models.CharField(max_length=200, blank=True, null=True, help_text="文件名")
    file_type = models.CharField(max_length=50, blank=True, null=True, help_text="文件类型")
    size = models.IntegerField(blank=True, null=True, help_text="文件大小（字节）")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    def __str__(self):
        return f"文档-{self.title[:20]}"
