import uuid
from django.db import models


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    payment_id = models.CharField(max_length=20, unique=True, editable=False)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='payments')
    paypal_order_id = models.CharField(max_length=100, blank=True)
    paypal_payer_id = models.CharField(max_length=100, blank=True)
    paypal_transaction_id = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    payment_method = models.CharField(max_length=50, default='PayPal')
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['paypal_order_id'], name='pay_paypal_idx'),
            models.Index(fields=['order', '-created_at'], name='pay_order_idx'),
        ]

    def __str__(self):
        return f"P-{self.payment_id} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)
