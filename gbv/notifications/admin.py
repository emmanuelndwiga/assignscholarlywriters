# notifications/admin.py
from django.contrib import admin

from .models import Notification, PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("owner", "endpoint", "created_at")
    search_fields = ("endpoint", "user__username", "case__reference_number")
    readonly_fields = ("created_at",)

    def owner(self, obj):
        return str(obj.user or obj.case)
    owner.short_description = "Owner"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("case", "channel", "recipient_user", "status", "created_at", "sent_at")
    list_filter = ("channel", "status", "created_at")
    search_fields = ("case__reference_number", "message", "recipient_user__username")
    readonly_fields = ("created_at", "sent_at")
