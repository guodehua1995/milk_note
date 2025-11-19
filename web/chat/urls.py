from django.urls import path
from . import views

app_name = 'chat'  # 设置应用命名空间

urlpatterns = [
    path('api/chat/', views.chat, name='chat'),
    path('api/conversations/', views.get_conversations, name='get_conversations'),
    path('api/profile/update/', views.update_profile, name='update_profile'),
    path('preferences/', views.ChatPreferenceView.as_view(), name='preferences'),  # 聊天偏好设置页面
]