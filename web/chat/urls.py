from django.urls import path
from . import views

app_name = 'chat'  # 设置应用命名空间

urlpatterns = [
    # 页面路由
    path('', views.ChatView.as_view(), name='chat'),  # 聊天页面
    path('issues/', views.IssueListView.as_view(), name='issues'),  # 事项列表页面
    path('issue/create/', views.IssueCreateView.as_view(), name='issue_create'),  # 创建事项页面
    path('issue/<int:pk>/', views.IssueDetailView.as_view(), name='issue_detail'),  # 事项详情页面
    path('issue/<int:pk>/update/', views.IssueUpdateView.as_view(), name='issue_update'),  # 更新事项页面
    path('preferences/', views.ChatPreferenceView.as_view(), name='preferences'),  # 聊天偏好设置页面
    
    # API路由
    path('api/chat/', views.chat_api, name='chat_api'),  # 聊天API
    path('api/conversations/', views.get_conversations, name='get_conversations'),  # 获取会话列表API
    path('api/conversation/<int:conversation_id>/', views.get_conversation_detail, name='get_conversation_detail'),  # 获取会话详情API
    path('api/profile/update/', views.update_profile, name='update_profile'),  # 更新用户资料API
]