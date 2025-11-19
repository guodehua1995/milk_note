from django.urls import path
from . import views

urlpatterns = [
    # 基本认证路由
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    
    # 用户信息管理路由
    path("profile/", views.profile_view, name="profile"),
    path("preferences/", views.preferences_view, name="preferences"),
    
    # API路由
    path("api/user-info/", views.api_user_info, name="api_user_info"),
    path("api/update-preferences/", views.api_update_preferences, name="api_update_preferences"),
]