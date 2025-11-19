from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User, UserProfile, UserPreference


class CustomUserChangeForm(UserChangeForm):
    """自定义用户编辑表单"""
    class Meta(UserChangeForm.Meta):
        model = User


class CustomUserCreationForm(UserCreationForm):
    """自定义用户创建表单"""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """自定义用户模型的管理界面"""
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    model = User
    
    list_display = ('username', 'email', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户个人信息的管理界面"""
    list_display = ('user', 'company', 'position', 'location')
    search_fields = ('user__username', 'user__email', 'company', 'position', 'location')
    list_filter = ('company', 'position', 'location')


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    """用户偏好设置的管理界面"""
    list_display = ('user', 'theme', 'language', 'notifications_enabled')
    search_fields = ('user__username', 'user__email')
    list_filter = ('theme', 'language', 'notifications_enabled', 'email_notifications', 'auto_save')
