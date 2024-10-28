from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Message, Task

# Register your custom User model
admin.site.register(User, UserAdmin)

from .models import ChatSession

class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')  # Displaying session ID and creation time
    search_fields = ('id',)  # Allow searching by ChatSession ID
    filter_horizontal = ('participants',)  # For ManyToMany fields

admin.site.register(ChatSession, ChatSessionAdmin)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat_session', 'sender', 'timestamp', 'read')  # Display relevant fields
    list_filter = ('read', 'timestamp')  # Filters to quickly view read/unread messages
    search_fields = ('sender__username', 'content')  # Search by sender username and message content

admin.site.register(Message, MessageAdmin)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_name', 'user', 'created_at')
    search_fields = ('task_name', 'description', 'user__username')
    list_filter = ('created_at', 'user')