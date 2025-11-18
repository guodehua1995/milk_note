from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from chat.services.memory_manager import MemoryManager
from chat.llm.chat_service import LangChainChatService

@csrf_exempt
def chat(request):
    """聊天接口"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            message = data.get('message')
            conversation_id = data.get('conversation_id')
            
            if not user_id or not message:
                return JsonResponse({'error': '缺少必要参数'}, status=400)
            
            # 调用聊天服务
            chat_service = LangChainChatService()
            result = chat_service.chat(user_id, message, conversation_id)
            
            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({'error': '无效的JSON格式'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '只支持POST请求'}, status=405)

@csrf_exempt
def get_conversations(request):
    """获取用户会话列表"""
    if request.method == 'GET':
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
