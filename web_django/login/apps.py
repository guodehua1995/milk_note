from django.apps import AppConfig
from django.db.models.signals import post_save


class LoginConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'login'
    
    def ready(self):
        # 导入信号处理函数
        from . import signals
        # 连接信号
        from django.contrib.auth import get_user_model
        User = get_user_model()
        post_save.connect(signals.create_user_profile, sender=User)
        post_save.connect(signals.create_user_preference, sender=User)
