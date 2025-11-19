"""
信号处理模块，用于处理用户模型相关的信号
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile, UserPreference


@receiver(post_save, sender=get_user_model())
def create_user_profile(sender, instance, created, **kwargs):
    """
    当用户创建时，自动创建对应的UserProfile
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=get_user_model())
def create_user_preference(sender, instance, created, **kwargs):
    """
    当用户创建时，自动创建对应的UserPreference
    """
    if created:
        UserPreference.objects.create(user=instance)


@receiver(post_save, sender=get_user_model())
def save_user_profile(sender, instance, **kwargs):
    """
    当用户保存时，自动保存对应的UserProfile
    """
    instance.profile.save()


@receiver(post_save, sender=get_user_model())
def save_user_preference(sender, instance, **kwargs):
    """
    当用户保存时，自动保存对应的UserPreference
    """
    instance.preferences.save()