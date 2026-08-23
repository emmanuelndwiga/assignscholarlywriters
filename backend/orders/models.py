import uuid
from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.CharField(max_length=20, unique=True, editable=False)
    quotation = models.OneToOneField('quotations.Quotation', on_delete=models.SET_NULL, null=True, blank=True, related_name='order')
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='orders')
    service = models.ForeignKey('services.ServiceType', on_delete=models.SET_NULL, null=True, related_name='orders')
    academic_level = models.ForeignKey('services.AcademicLevel', on_delete=models.SET_NULL, null=True, related_name='orders')
    pages = models.PositiveIntegerField(default=1)
    words = models.PositiveIntegerField(default=275)
    deadline = models.ForeignKey('pricing.DeadlineMultiplier', on_delete=models.SET_NULL, null=True, related_name='orders')
    course_subject = models.CharField(max_length=200, blank=True)
    specifications = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ORD-{self.order_id}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)
