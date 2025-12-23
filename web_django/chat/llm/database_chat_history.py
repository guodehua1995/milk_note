from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (BaseMessage, HumanMessage, 
                                     AIMessage, SystemMessage, ToolMessage)
from chat.models import ChatMessage
import uuid
from django.utils import timezone

class DatabaseChatMessageHistory(BaseChatMessageHistory):
    """基于数据库的聊天历史存储实现，直接关联用户和事项，去掉会话概念"""
    
    def __init__(self, user_id, issue_id=None):
        """初始化数据库聊天历史
        
        Args:
            user_id: 用户ID
            issue_id: 事项ID，如果为None则表示无事项的聊天
        """
        self.user_id = user_id
        self.issue_id = issue_id
    
    @property
    def messages(self):
        """从数据库获取消息列表"""
        # 根据用户ID和事项ID过滤消息
        filters = {'user_id': self.user_id}
        if self.issue_id:
            filters['issue_id'] = self.issue_id
        
        message_objects = ChatMessage.objects.filter(**filters).order_by('created_at')
        messages = []
        
        for msg_obj in message_objects:
            if msg_obj.role == 'user':
                msg = HumanMessage(content=msg_obj.content)
            elif msg_obj.role == 'assistant':
                msg = AIMessage(content=msg_obj.content)
            elif msg_obj.role == 'system':
                msg = SystemMessage(content=msg_obj.content)
            elif msg_obj.role == 'tool':
                msg = ToolMessage(content=msg_obj.content)
            else:
                continue
            
            messages.append(msg)
        
        return messages
    
    def add_message(self, message: BaseMessage) -> None:
        """添加消息到数据库"""
        # 正确映射消息类型到角色
        if isinstance(message, HumanMessage):
            role = 'user'
        elif isinstance(message, AIMessage):
            role = 'assistant'
        elif isinstance(message, SystemMessage):
            role = 'system'
        elif isinstance(message, ToolMessage):
            role = 'tool'
        else:
            # 如果是其他类型的消息，尝试从消息对象中获取角色
            role = getattr(message, 'role', 'user')
        
        # 直接创建ChatMessage，关联用户和事项，去掉会话
        ChatMessage.objects.create(
            user_id=self.user_id,
            issue_id=self.issue_id,
            role=role,
            content=message.content,
            message_id=str(uuid.uuid4()),
            metadata=getattr(message, 'metadata', {})
        )
    
    def clear(self) -> None:
        """清空当前聊天历史"""
        # 根据用户ID和事项ID过滤消息
        filters = {'user_id': self.user_id}
        if self.issue_id:
            filters['issue_id'] = self.issue_id
        
        ChatMessage.objects.filter(**filters).delete()
    
    def get_conversation_id(self):
        """获取当前会话标识，使用用户ID和事项ID组合"""
        # 去掉会话概念后，使用用户ID和事项ID组合作为会话标识
        return f"{self.user_id}_{self.issue_id if self.issue_id else 'none'}"
    
    def update_conversation_title(self, title):
        """更新会话标题，去掉会话概念后此方法不再使用"""
        pass