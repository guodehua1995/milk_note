import json
import logging
from django.http import JsonResponse, HttpResponseRedirect, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, ListView, CreateView, DetailView, UpdateView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.forms.widgets import RadioSelect
from django.shortcuts import render, get_object_or_404
import json
from chat.services.memory_manager import MemoryManager
from chat.llm.chat_service import LangChainChatService
from chat.models import UserChatProfile, Conversation, ChatMessage, Issue
from django.utils import timezone

# 配置日志
logger = logging.getLogger(__name__)

# 聊天页面视图
class ChatView(LoginRequiredMixin, FormView):
    """
    聊天页面视图，展示聊天界面并处理聊天请求
    """
    template_name = 'chat.html'
    form_class = None
    
    def get(self, request, *args, **kwargs):
        # 获取当前用户的所有事项
        issues = Issue.objects.filter(user=request.user)
        
        # 获取当前事项（如果有）
        current_issue = None
        issue_id = request.GET.get('issue_id')
        if issue_id:
            current_issue = get_object_or_404(Issue, id=issue_id, user=request.user)
        
        return render(request, self.template_name, {
            'issues': issues,
            'current_issue': current_issue
        })

@csrf_exempt
def chat_api(request):
    """聊天接口，支持流式输出"""
    if request.method == 'POST':
        try:
            logger.info("收到聊天请求")
            data = json.loads(request.body)
            logger.info(f"请求数据: {data}")
            
            # 确保用户已认证
            if not request.user.is_authenticated:
                return JsonResponse({'error': '用户未认证'}, status=401)
            
            user_id = request.user.id
            message = data.get('message')
            conversation_id = data.get('conversation_id')
            issue_id = data.get('issue_id')
            stream = data.get('stream', False)  # 是否使用流式输出
            
            logger.info(f"用户ID: {user_id}, 消息: {message}, 会话ID: {conversation_id}, 事项ID: {issue_id}, 流式: {stream}")
            
            if not message:
                logger.error("缺少必要参数")
                return JsonResponse({'error': '缺少必要参数'}, status=400)
            
            # 获取或创建会话
            conversation = None
            if conversation_id:
                conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
            else:
                # 创建新会话
                conversation = Conversation.objects.create(
                    user=request.user,
                    title="新对话"
                )
                
                # 如果有事项，关联到会话
                if issue_id:
                    issue = get_object_or_404(Issue, id=issue_id, user=request.user)
                    conversation.issue = issue
                    conversation.save()
            
            # 调用聊天服务
            chat_service = LangChainChatService()
            logger.info("已创建聊天服务实例")
            
            # 获取事项长期记忆（如果有）
            system_prompt = ""
            if conversation.issue and conversation.issue.long_term_memory:
                system_prompt = conversation.issue.long_term_memory
            
            # 非流式输出
            if not stream:
                logger.info("开始非流式聊天处理")
                result = chat_service.chat(user_id, message, conversation.id, system_prompt=system_prompt)
                logger.info("非流式输出结果: %s", result)
                logger.info("结果类型: %s", type(result))
                
                # 检查result中的每个字段
                if isinstance(result, dict):
                    for key, value in result.items():
                        logger.info("字段 %s 的类型: %s, 值: %s", key, type(value), value)
                
                # 尝试手动序列化结果
                try:
                    import json as json_module
                    json_module.dumps(result)
                    logger.info("结果可以被JSON序列化")
                except Exception as serialize_error:
                    logger.error("结果无法被JSON序列化: %s", str(serialize_error))
                    return JsonResponse({'error': f'序列化错误: {str(serialize_error)}'}, status=500)
                
                # 添加会话ID到结果中
                result['conversation_id'] = conversation.id
                
                return JsonResponse(result)
            
            # 流式输出 - 使用StreamingHttpResponse
            def stream_generator():
                try:
                    # 获取流式响应生成器
                    stream_response = chat_service.chat(user_id, message, conversation.id, stream=True, system_prompt=system_prompt)
                    
                    # 逐个发送每个响应片段
                    for chunk_data in stream_response:
                        # 确保chunk_data是字典格式
                        if isinstance(chunk_data, dict):
                            # 发送SSE格式的数据
                            chunk_json = json.dumps(chunk_data, ensure_ascii=False)
                            yield f"data: {chunk_json}\n\n"
                        else:
                            # 如果不是字典，尝试转换
                            try:
                                chunk_dict = chunk_data if isinstance(chunk_data, dict) else {"chunk": str(chunk_data)}
                                chunk_json = json.dumps(chunk_dict, ensure_ascii=False)
                                yield f"data: {chunk_json}\n\n"
                            except Exception as convert_error:
                                error_data = json.dumps({
                                    'error': f"数据转换错误: {str(convert_error)}",
                                    'is_complete': True
                                }, ensure_ascii=False)
                                yield f"data: {error_data}\n\n"
                except Exception as e:
                    # 发生错误时发送错误信息
                    error_data = json.dumps({
                        'error': str(e),
                        'is_complete': True
                    }, ensure_ascii=False)
                    yield f"data: {error_data}\n\n"
            
            # 创建流式响应
            response = StreamingHttpResponse(stream_generator(), content_type='text/event-stream')
            response['Cache-Control'] = 'no-cache'
            return response
            
        except json.JSONDecodeError:
            return JsonResponse({'error': '无效的JSON格式'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '只支持POST请求'}, status=405)

@csrf_exempt
def get_conversations(request):
    """获取用户会话列表"""
    if request.method == 'GET':
        # 确保用户已认证
        if not request.user.is_authenticated:
            return JsonResponse({'error': '用户未认证'}, status=401)
        
        # 从数据库获取会话列表
        conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
        
        # 构建响应数据
        conversations_data = []
        for conversation in conversations:
            # 获取最后一条消息
            last_message = conversation.messages.last()
            last_message_content = last_message.content[:50] + '...' if last_message else '无消息'
            
            conversations_data.append({
                'id': conversation.id,
                'title': conversation.title,
                'last_message': last_message_content,
                'updated_at': conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({'conversations': conversations_data})
    
    return JsonResponse({'error': '只支持GET请求'}, status=405)

@csrf_exempt
def get_conversation_detail(request, conversation_id):
    """获取会话详情"""
    if request.method == 'GET':
        # 确保用户已认证
        if not request.user.is_authenticated:
            return JsonResponse({'error': '用户未认证'}, status=401)
        
        # 获取会话
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        
        # 获取会话消息
        messages = ChatMessage.objects.filter(conversation=conversation).order_by('created_at')
        
        # 构建响应数据
        messages_data = []
        for message in messages:
            messages_data.append({
                'role': message.role,
                'content': message.content,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'updated_at': conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            },
            'messages': messages_data
        })
    
    return JsonResponse({'error': '只支持GET请求'}, status=405)

@csrf_exempt
def update_profile(request):
    """更新用户资料"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # 优先使用已认证用户的id，保持向后兼容
            user_id = None
            if request.user.is_authenticated:
                user_id = request.user.id
            else:
                user_id = data.get('user_id')
                
            if not user_id:
                return JsonResponse({'error': '缺少用户ID'}, status=400)
            
            memory_manager = MemoryManager(user_id)
            memory_manager.update_user_profile(
                name=data.get('name'),
                key_points=data.get('key_points'),
                preferences=data.get('preferences')
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '只支持POST请求'}, status=405)


class ChatPreferenceForm(forms.Form):
    """
    聊天偏好设置表单
    用于收集用户的聊天风格偏好和昵称
    """
    name = forms.CharField(
        label='您的昵称',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入您的昵称'})
    )
    
    assistant_name = forms.CharField(
        label='您的助手昵称',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入助手昵称'})
    )
    
    extra_notice = forms.CharField(
        label='注意事项',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入注意事项'})
    )
    
    key_points = forms.CharField(
        label='记忆要点',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': '请输入记忆要点', 'rows': 3})
    )
    
    # 使用隐藏字段存储偏好设置JSON数据
    preferences = forms.CharField(widget=forms.HiddenInput, required=False)
    
    def clean(self):
        """
        清理表单数据，将radio选项合并到preferences JSON中
        """
        cleaned_data = super().clean()
        # 从请求中获取聊天风格偏好
        style = self.data.get('preferences_style', 'general')  # 默认通用风格
        
        # 创建或更新preferences字典
        preferences = cleaned_data.get('preferences', '{}')
        try:
            preferences_dict = json.loads(preferences) if preferences else {}
        except json.JSONDecodeError:
            preferences_dict = {}
        
        # 更新风格设置
        preferences_dict['style'] = style
        
        # 将更新后的字典转换回JSON字符串
        cleaned_data['preferences'] = json.dumps(preferences_dict)
        
        return cleaned_data


# 事项相关视图
class IssueListView(LoginRequiredMixin, ListView):
    """
    事项列表视图
    展示用户的所有事项
    """
    model = Issue
    template_name = 'issue.html'
    context_object_name = 'issues'
    
    def get_queryset(self):
        # 只返回当前用户的事项
        return Issue.objects.filter(user=self.request.user).order_by('-updated_at')

class IssueCreateView(LoginRequiredMixin, CreateView):
    """
    事项创建视图
    用于创建新事项
    """
    model = Issue
    template_name = 'issue_form.html'
    fields = ['title', 'description', 'status']
    success_url = reverse_lazy('chat:issues')
    
    def form_valid(self, form):
        # 设置事项的用户为当前登录用户
        form.instance.user = self.request.user
        return super().form_valid(form)

class IssueDetailView(LoginRequiredMixin, DetailView):
    """
    事项详情视图
    展示事项的详细信息
    """
    model = Issue
    template_name = 'issue_detail.html'
    context_object_name = 'issue'
    
    def get_queryset(self):
        # 只返回当前用户的事项
        return Issue.objects.filter(user=self.request.user)

class IssueUpdateView(LoginRequiredMixin, UpdateView):
    """
    事项更新视图
    用于更新事项信息
    """
    model = Issue
    template_name = 'issue_form.html'
    fields = ['title', 'description', 'status']
    success_url = reverse_lazy('chat:issues')
    
    def get_queryset(self):
        # 只返回当前用户的事项
        return Issue.objects.filter(user=self.request.user)

# 聊天偏好设置视图
class ChatPreferenceView(LoginRequiredMixin, FormView):
    """
    聊天偏好设置视图
    展示并处理用户的聊天偏好设置表单
    """
    template_name = 'chat_preference.html'
    form_class = ChatPreferenceForm
    
    def get_initial(self):
        """
        获取初始表单数据，从用户的UserChatProfile中加载
        """
        initial = super().get_initial()
        user = self.request.user
        
        try:
            # 获取用户的聊天配置文件
            chat_profile = UserChatProfile.objects.get(user=user)
            # 设置初始昵称
            initial['name'] = chat_profile.name
            # 设置初始助手昵称
            initial['assistant_name'] = chat_profile.assistant_name
            # 设置初始注意事项
            initial['extra_notice'] = chat_profile.extra_notice
            # 设置初始记忆要点
            initial['key_points'] = chat_profile.key_points
            # 设置初始偏好设置
            initial['preferences'] = json.dumps({'style': chat_profile.style}) if chat_profile.style else '{}'
        except UserChatProfile.DoesNotExist:
            # 如果用户没有聊天配置文件，使用默认值
            initial['name'] = ''
            initial['assistant_name'] = '助手'
            initial['extra_notice'] = ''
            initial['key_points'] = ''
            initial['preferences'] = json.dumps({'style': 'general'})
        
        return initial
    
    def form_valid(self, form):
        """
        处理表单提交成功的情况，更新用户的聊天配置文件
        """
        user = self.request.user
        name = form.cleaned_data.get('name')
        assistant_name = form.cleaned_data.get('assistant_name')
        extra_notice = form.cleaned_data.get('extra_notice')
        key_points = form.cleaned_data.get('key_points')
        preferences = form.cleaned_data.get('preferences')
        
        # 解析preferences JSON字符串
        preferences_dict = json.loads(preferences) if preferences else {}
        
        # 获取风格设置
        style = preferences_dict.get('style', 'general')
        
        # 使用MemoryManager更新用户配置文件
        memory_manager = MemoryManager(user.id)
        memory_manager.update_user_profile(
            name=name,
            assistant_name=assistant_name,
            extra_notice=extra_notice,
            key_points=key_points,
            style=style
        )
        
        # 表单提交成功后重定向到当前页面，显示更新后的设置
        return HttpResponseRedirect(reverse('chat:preferences'))

# 更新事项长期记忆的视图（用于定时任务）
def update_issue_memory():
    """
    更新所有事项的长期记忆
    每30分钟在后台自动调用一次
    """
    # 获取所有进行中的事项
    issues = Issue.objects.filter(status='in_progress')
    
    for issue in issues:
        # 检查是否需要更新记忆（超过30分钟）
        if timezone.now() - issue.last_memory_update > timezone.timedelta(minutes=30):
            # 获取该事项的所有聊天消息
            messages = ChatMessage.objects.filter(
                conversation__issue=issue
            ).order_by('created_at')
            
            # 构建消息历史
            message_history = []
            for message in messages:
                message_history.append({
                    'role': message.role,
                    'content': message.content
                })
            
            # 如果有消息历史，生成长期记忆
            if message_history:
                # 这里可以调用LLM来生成长期记忆
                # 简化处理：直接拼接所有消息内容
                memory_content = ''
                for msg in message_history:
                    memory_content += f"{msg['role']}: {msg['content']}\n"
                
                # 更新事项的长期记忆
                issue.long_term_memory = memory_content
                issue.last_memory_update = timezone.now()
                issue.save()
