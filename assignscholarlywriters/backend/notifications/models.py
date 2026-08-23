from django.db import models


class NotificationLog(models.Model):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    recipient = models.CharField(max_length=200)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    quotation = models.ForeignKey('quotations.Quotation', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='notif_status_idx'),
        ]

    def __str__(self):
        return f"{self.notification_type} to {self.recipient} ({self.status})"
