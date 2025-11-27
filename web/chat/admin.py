from django.contrib import admin

# Register your models here.
from .models import (ChatMessage,
                     UserChatProfile,
                     Issue)
admin.site.register(ChatMessage)
admin.site.register(UserChatProfile)
admin.site.register(Issue)
