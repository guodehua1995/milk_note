from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm

def login_view(request):
    """处理用户登录"""
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'{username} 登录成功！')
                return redirect('accounts:dashboard')
            else:
                messages.error(request, '用户名或密码错误')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def dashboard(request):
    """用户登录后的仪表板页面"""
    return render(request, 'accounts/dashboard.html', {'user': request.user})

def logout_view(request):
    """用户登出"""
    logout(request)
    messages.info(request, '您已成功登出')
    return redirect('accounts:login')
