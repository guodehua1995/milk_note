#!/usr/bin/env python
"""全面测试UserChatProfile模型的新字段和相关功能"""

import os
import sys
import django
from django.conf import settings

# 添加项目路径
sys.path.append('d:/personal_projects/milk_note/web')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'milk_note.settings')
django.setup()

from chat.models import UserChatProfile
from login.models import User
from chat.services.memory_manager import MemoryManager

def test_user_chat_profile():
    print("=== 测试UserChatProfile模型 ===")
    # 创建一个测试用户
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com'
        }
    )
    
    # 获取或创建用户的聊天配置
    profile, created = UserChatProfile.objects.get_or_create(
        user=user,
        defaults={
            'name': '测试用户',
            'style': 'friendly',
            'assistant_name': '小助手',
            'extra_notice': '这是一个测试注意事项'
        }
    )
    
    # 打印当前配置
    print(f"用户: {profile.user.username}")
    print(f"名称: {profile.name}")
    print(f"风格: {profile.style}")
    print(f"助手名称: {profile.assistant_name}")
    print(f"注意事项: {profile.extra_notice}")
    
    # 更新配置
    profile.style = 'professional'
    profile.assistant_name = '专业助手'
    profile.extra_notice = '这是更新后的注意事项'
    profile.save()
    
    # 再次打印更新后的配置
    print("\n更新后:")
    print(f"风格: {profile.style}")
    print(f"助手名称: {profile.assistant_name}")
    print(f"注意事项: {profile.extra_notice}")
    
    print("\n=== 测试MemoryManager ===")
    # 测试MemoryManager
    memory_manager = MemoryManager(user.id)
    
    # 获取长期记忆
    long_term_memory = memory_manager.get_long_term_memory()
    print(f"长期记忆: {long_term_memory}")
    
    # 更新用户配置文件
    memory_manager.update_user_profile(
        name="更新后的用户",
        style="childhood",
        assistant_name="儿童助手",
        extra_notice="这是儿童模式的注意事项"
    )
    
    # 再次获取长期记忆
    updated_long_term_memory = memory_manager.get_long_term_memory()
    print(f"更新后的长期记忆: {updated_long_term_memory}")
    
    print("\n=== 验证字段长度限制 ===")
    # 测试字段长度限制
    try:
        # 测试style字段（最多20字）
        profile.style = 'a' * 25  # 超过20个字符
        profile.save()
        print("警告：style字段应该限制在20个字符以内")
    except Exception as e:
        print(f"style字段长度限制正常: {e}")
    
    try:
        # 测试assistant_name字段（最多10个字）
        profile.assistant_name = 'a' * 15  # 超过10个字符
        profile.save()
        print("警告：assistant_name字段应该限制在10个字符以内")
    except Exception as e:
        print(f"assistant_name字段长度限制正常: {e}")
    
    try:
        # 测试extra_notice字段（最多200字）
        profile.extra_notice = 'a' * 250  # 超过200个字符
        profile.save()
        print("警告：extra_notice字段应该限制在200个字符以内")
    except Exception as e:
        print(f"extra_notice字段长度限制正常: {e}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_user_chat_profile()