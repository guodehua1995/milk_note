from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (BaseMessage, HumanMessage, AIMessage,
                                     SystemMessage, ToolMessage)
from chat.models import Conversation, ChatMessage
import uuid
from django.utils import timezone

class DatabaseChatMessageHistory(BaseChatMessageHistory):
    """基于数据库的聊天历史存储实现"""
    
    def __init__(self, user_id, conversation_id=None, create_if_not_exists=True):
        """初始化数据库聊天历史
        
        Args:
            user_id: 用户标识
            conversation_id: 会话ID，如果为None则创建新会话
            create_if_not_exists: 如果会话不存在是否创建新会话
        """
        self.user_id = user_id
        self.conversation = None
        
        if conversation_id:
            try:
                self.conversation = Conversation.objects.get(id=conversation_id, user_id=user_id)
            except Conversation.DoesNotExist:
                if create_if_not_exists:
                    self.conversation = self._create_new_conversation()
        else:
            self.conversation = self._create_new_conversation()
    
    def _create_new_conversation(self):
        """创建新的会话"""
        return Conversation.objects.create(
            user_id=self.user_id,
            title=f"新对话-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        )
    
    @property
    def messages(self):
        """从数据库获取消息列表"""
        message_objects = ChatMessage.objects.filter(conversation=self.conversation)
        messages = []
        
        for msg_obj in message_objects:
            if msg_obj.role == 'human':
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
        role_map = {
            'HumanMessage': 'user',
            'AIMessage': 'assistant', 
            'SystemMessage': 'system',
            'ToolMessage': 'tool'
        }
        
        role = role_map.get(message.__class__.__name__, 'user')
        
        ChatMessage.objects.create(
            conversation=self.conversation,
            role=role,
            content=message.content,
            message_id=str(uuid.uuid4()),
            metadata=getattr(message, 'metadata', {})
        )
        
        # 更新会话的最后更新时间
        self.conversation.updated_at = timezone.now()
        self.conversation.save()
    
    def clear(self) -> None:
        """清空当前会话的消息"""
        ChatMessage.objects.filter(conversation=self.conversation).delete()
    
    def get_conversation_id(self):
        """获取当前会话ID"""
        return self.conversation.id
    
    def update_conversation_title(self, title):
        """更新会话标题"""
        self.conversation.title = title
        self.conversation.save()