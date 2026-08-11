# notifications/models.py
from django.db import models


class PushSubscription(models.Model):
    """A browser's web push subscription. Owner is either a staff User OR a case
    (victim), never both — victims have no account, so we key their subscription
    to the case they're tracking."""

    user = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.CASCADE, related_name="push_subscriptions"
    )
    case = models.ForeignKey(
        "cases.CaseReport", null=True, blank=True, on_delete=models.CASCADE, related_name="push_subscriptions"
    )

    endpoint = models.URLField(max_length=500, unique=True)
    p256dh_key = models.CharField(max_length=255)
    auth_key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, case__isnull=True)
                    | models.Q(user__isnull=True, case__isnull=False)
                ),
                name="push_subscription_exactly_one_owner",
            )
        ]

    def __str__(self):
        owner = self.user or self.case
        return f"Subscription for {owner}"


class Notification(models.Model):
    class Channel(models.TextChoices):
        PUSH = "push", "Web Push"
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    case = models.ForeignKey("cases.CaseReport", on_delete=models.CASCADE, related_name="notifications")
    update = models.ForeignKey(
        "cases.CaseUpdate", null=True, blank=True, on_delete=models.SET_NULL, related_name="notifications"
    )
    recipient_user = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="notifications"
    )  # null when the recipient is the victim rather than staff

    channel = models.CharField(max_length=10, choices=Channel.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    message = models.CharField(max_length=255)  # the neutral nudge text actually sent, kept for audit
    error_detail = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_channel_display()} to {self.recipient_user or 'victim'} - {self.status}"