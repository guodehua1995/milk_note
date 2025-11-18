from django.urls import path
from . import views

urlpatterns = [
    path('api/chat/', views.chat, name='chat'),
    path('api/conversations/', views.get_conversations, name='get_conversations'),
    path('api/profile/update/', views.update_profile, name='update_profile'),
]