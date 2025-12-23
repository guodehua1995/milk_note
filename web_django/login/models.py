from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings


class UserManager(BaseUserManager):
    """
    自定义用户管理器，用于处理用户创建和验证
    """
    def create_user(self, username, email, password=None, **extra_fields):
        """创建并保存普通用户"""
        if not email:
            raise ValueError('用户必须有邮箱地址')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """创建并保存超级用户"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    自定义用户模型，替代Django默认的User模型
    """
    username = models.CharField(max_length=100, unique=True, help_text="用户名")
    email = models.EmailField(max_length=255, unique=True, help_text="邮箱地址")
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="手机号码")
    first_name = models.CharField(max_length=100, blank=True, null=True, help_text="名字")
    last_name = models.CharField(max_length=100, blank=True, null=True, help_text="姓氏")
    is_active = models.BooleanField(default=True, help_text="是否激活")
    is_staff = models.BooleanField(default=False, help_text="是否为管理员")
    date_joined = models.DateTimeField(auto_now_add=True, help_text="注册时间")
    last_login = models.DateTimeField(blank=True, null=True, help_text="最后登录时间")
    
    objects = UserManager()
    
    # 指定用户名字段为email
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        """获取用户的全名"""
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def get_short_name(self):
        """获取用户的短名称"""
        return self.first_name or self.username


class UserPreference(models.Model):
    """
    用户偏好设置模型
    存储用户的各种个性化配置
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences', help_text="关联的用户")
    theme = models.CharField(max_length=20, default='light', choices=[('light', '浅色主题'), ('dark', '深色主题')], help_text="界面主题")
    language = models.CharField(max_length=10, default='zh-cn', choices=[('zh-cn', '简体中文'), ('en-us', '英文')], help_text="语言偏好")
    notifications_enabled = models.BooleanField(default=True, help_text="是否启用通知")
    email_notifications = models.BooleanField(default=True, help_text="是否启用邮件通知")
    auto_save = models.BooleanField(default=True, help_text="是否自动保存")
    other_settings = models.JSONField(default=dict, help_text="其他设置")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    def __str__(self):
        return f"{self.user.username}的偏好设置"


class UserProfile(models.Model):
    """
    用户个人信息模型
    存储用户的详细个人资料
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile', help_text="关联的用户")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, help_text="头像")
    bio = models.TextField(blank=True, null=True, help_text="个人简介")
    company = models.CharField(max_length=200, blank=True, null=True, help_text="公司")
    position = models.CharField(max_length=200, blank=True, null=True, help_text="职位")
    website = models.URLField(blank=True, null=True, help_text="个人网站")
    location = models.CharField(max_length=200, blank=True, null=True, help_text="所在地")
    created_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")
    
    def __str__(self):
        return f"{self.user.username}的个人资料"
