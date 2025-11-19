"""
表单定义模块，包含登录、注册和个人信息管理相关表单
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile, UserPreference

User = get_user_model()


class CustomAuthenticationForm(AuthenticationForm):
    """
    自定义登录表单
    添加记住我功能
    """
    remember_me = forms.BooleanField(required=False, initial=False, label="记住我")
    
    class Meta:
        model = User
        fields = ('username', 'password', 'remember_me')


class CustomUserCreationForm(UserCreationForm):
    """
    自定义用户注册表单
    添加邮箱和其他必要字段
    """
    email = forms.EmailField(required=True, help_text="必填，请输入有效的邮箱地址")
    first_name = forms.CharField(max_length=100, required=False, help_text="选填")
    last_name = forms.CharField(max_length=100, required=False, help_text="选填")
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """
    用户基本信息更新表单
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UserProfileUpdateForm(forms.ModelForm):
    """
    用户详细个人信息更新表单
    """
    class Meta:
        model = UserProfile
        fields = ('avatar', 'bio', 'company', 'position', 'website', 'location')
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UserPreferenceForm(forms.ModelForm):
    """
    用户偏好设置表单
    """
    class Meta:
        model = UserPreference
        fields = ('theme', 'language', 'notifications_enabled', 'email_notifications', 'auto_save', 'other_settings')
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'notifications_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_save': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'other_settings': forms.Textarea(attrs={'class': 'form-control'}),
        }