from django.contrib import admin
from .models import Notification

class NotificationAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ['title', 'recipient', 'notification_type', 'is_read', 'created_at']
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_filter = ['notification_type', 'is_read', 'created_at']
    # pyrefly: ignore [bad-override-mutable-attribute]
    search_fields = ['title', 'message', 'recipient__username']
    # pyrefly: ignore [bad-override-mutable-attribute]
    readonly_fields = ['created_at']
    list_per_page = 30

    # pyrefly: ignore [bad-override-mutable-attribute]
    actions = ['mark_as_read']

    @admin.action(description='Mark selected as read')
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"Marked {queryset.count()} notifications as read.")

admin.site.register(Notification, NotificationAdmin)
