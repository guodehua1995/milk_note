import json
import logging
from django.http import JsonResponse, HttpResponseRedirect, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.forms.widgets import RadioSelect
import json
from chat.services.memory_manager import MemoryManager
from chat.llm.chat_service import LangChainChatService
from chat.models import UserChatProfile

# 配置日志
logger = logging.getLogger(__name__)

@csrf_exempt
def chat(request):
    """聊天接口，支持流式输出"""
    if request.method == 'POST':
        try:
            logger.info("收到聊天请求")
            data = json.loads(request.body)
            logger.info(f"请求数据: {data}")
            # 优先使用已认证用户的id，保持向后兼容
            user_id = None
            if request.user.is_authenticated:
                user_id = request.user.id
            else:
                user_id = data.get('user_id')
            
            message = data.get('message')
            conversation_id = data.get('conversation_id')
            stream = data.get('stream', False)  # 是否使用流式输出
            
            logger.info(f"用户ID: {user_id}, 消息: {message}, 会话ID: {conversation_id}, 流式: {stream}")
            
            if not user_id or not message:
                logger.error("缺少必要参数")
                return JsonResponse({'error': '缺少必要参数'}, status=400)
            
            # 调用聊天服务
            chat_service = LangChainChatService()
            logger.info("已创建聊天服务实例")
            
            # 非流式输出
            if not stream:
                logger.info("开始非流式聊天处理")
                result = chat_service.chat(user_id, message, conversation_id)
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
                
                return JsonResponse(result)
            
            # 流式输出 - 使用StreamingHttpResponse
            def stream_generator():
                try:
                    # 获取流式响应生成器
                    stream_response = chat_service.chat(user_id, message, conversation_id, stream=True)
                    
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
        # 优先使用已认证用户的id，保持向后兼容
        user_id = None
        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = request.GET.get('user_id')
            
        if not user_id:
            return JsonResponse({'error': '缺少用户ID'}, status=400)
        
        memory_manager = MemoryManager(user_id)
        conversations = memory_manager.get_user_conversations(include_messages=False)
        
        return JsonResponse({'conversations': conversations})
    
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
            print(f"获取到用户自定义配置:{chat_profile.preferences}")
            # 设置初始昵称
            initial['name'] = chat_profile.name
            # 设置初始偏好设置
            initial['preferences'] = json.dumps(chat_profile.preferences or {})
        except UserChatProfile.DoesNotExist:
            # 如果用户没有聊天配置文件，使用默认值
            initial['name'] = ''
            initial['preferences'] = json.dumps({'style': 'general'})
        
        return initial
    
    def form_valid(self, form):
        """
        处理表单提交成功的情况，更新用户的聊天配置文件
        """
        user = self.request.user
        name = form.cleaned_data.get('name')
        preferences = form.cleaned_data.get('preferences')
        
        # 解析preferences JSON字符串
        preferences_dict = json.loads(preferences) if preferences else {}
        
        # 使用MemoryManager更新用户配置文件
        memory_manager = MemoryManager(user.id)
        memory_manager.update_user_profile(
            name=name,
            preferences=preferences_dict
        )
        
        # 表单提交成功后重定向到当前页面，显示更新后的设置
        return HttpResponseRedirect(reverse('chat:preferences'))
