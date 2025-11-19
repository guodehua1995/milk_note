from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from .forms import (
    CustomAuthenticationForm, 
    CustomUserCreationForm, 
    UserUpdateForm, 
    UserProfileUpdateForm, 
    UserPreferenceForm
)
from django.contrib.auth import get_user_model

User = get_user_model()


def index(request):
    """
    登录应用首页
    如果用户已登录，重定向到个人信息页面
    否则重定向到登录页面
    """
    if request.user.is_authenticated:
        return redirect('login:profile')
    return redirect('login:login')


def login_view(request):
    """
    用户登录视图
    处理用户登录请求，支持记住我功能
    """
    if request.user.is_authenticated:
        return redirect('login:profile')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                
                # 更新最后登录时间
                user.last_login = timezone.now()
                user.save()
                
                # 设置会话过期时间（记住我功能）
                if remember_me:
                    request.session.set_expiry(1209600)  # 2周
                else:
                    request.session.set_expiry(0)  # 浏览器关闭时过期
                
                # 检查是否有next参数
                next_url = request.GET.get('next', 'login:profile')
                return redirect(next_url)
        else:
            messages.error(request, '用户名或密码错误，请重试')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'login/login.html', {'form': form})


def register_view(request):
    """
    用户注册视图
    处理新用户注册请求
    """
    if request.user.is_authenticated:
        return redirect('login:profile')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 自动登录新创建的用户
            auth_login(request, user)
            messages.success(request, '注册成功，欢迎使用！')
            return redirect('login:profile')
        else:
            messages.error(request, '注册失败，请检查表单信息')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'login/register.html', {'form': form})


def logout_view(request):
    """
    用户登出视图
    处理用户登出请求
    """
    auth_logout(request)
    messages.success(request, '已成功登出')
    return redirect('login:login')


@login_required
def profile_view(request):
    """
    用户个人信息视图
    显示并允许更新用户的个人信息
    """
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, '个人信息已更新')
            return redirect('login:profile')
        else:
            messages.error(request, '更新失败，请检查表单信息')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    
    return render(request, 'login/profile.html', context)


@login_required
def preferences_view(request):
    """
    用户偏好设置视图
    显示并允许更新用户的偏好设置
    """
    if request.method == 'POST':
        form = UserPreferenceForm(request.POST, instance=request.user.preferences)
        if form.is_valid():
            form.save()
            messages.success(request, '偏好设置已更新')
            return redirect('login:preferences')
        else:
            messages.error(request, '更新失败，请检查表单信息')
    else:
        form = UserPreferenceForm(instance=request.user.preferences)
    
    return render(request, 'login/preferences.html', {'form': form})


# API视图函数（用于前端AJAX调用）

@csrf_exempt
@login_required
def api_user_info(request):
    """
    获取当前用户信息的API
    返回用户的基本信息和个人资料
    """
    if request.method == 'GET':
        user = request.user
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'phone_number': user.phone_number,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'profile': {
                'bio': user.profile.bio,
                'company': user.profile.company,
                'position': user.profile.position,
                'website': user.profile.website,
                'location': user.profile.location,
                'avatar': user.profile.avatar.url if user.profile.avatar else None
            },
            'preferences': {
                'theme': user.preferences.theme,
                'language': user.preferences.language,
                'notifications_enabled': user.preferences.notifications_enabled,
                'email_notifications': user.preferences.email_notifications,
                'auto_save': user.preferences.auto_save
            }
        }
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required
def api_update_preferences(request):
    """
    更新用户偏好设置的API
    接受JSON格式的偏好设置数据
    """
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            preferences = request.user.preferences
            
            # 更新偏好设置
            if 'theme' in data:
                preferences.theme = data['theme']
            if 'language' in data:
                preferences.language = data['language']
            if 'notifications_enabled' in data:
                preferences.notifications_enabled = data['notifications_enabled']
            if 'email_notifications' in data:
                preferences.email_notifications = data['email_notifications']
            if 'auto_save' in data:
                preferences.auto_save = data['auto_save']
            if 'other_settings' in data:
                preferences.other_settings = data['other_settings']
            
            preferences.save()
            return JsonResponse({'success': True, 'message': '偏好设置已更新'})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)