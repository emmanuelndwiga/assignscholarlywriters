from django.contrib import admin
from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'recipient', 'subject', 'status', 'quotation', 'sent_at', 'created_at')
    list_filter = ('notification_type', 'status')
    search_fields = ('recipient', 'subject', 'message')
    readonly_fields = ('created_at', 'sent_at')
