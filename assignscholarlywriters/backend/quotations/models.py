import uuid
from django.db import models
from django.utils import timezone
from customers.models import Customer


def quotation_attachment_path(instance, filename):
    return f"quotations/{instance.quotation.request_id}/{filename}"


class Quotation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('quoted', 'Quoted'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('converted', 'Converted to Order'),
    ]

    request_id = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')

    service = models.ForeignKey('services.ServiceType', on_delete=models.SET_NULL, null=True, related_name='quotations')
    academic_level = models.ForeignKey('services.AcademicLevel', on_delete=models.SET_NULL, null=True, related_name='quotations')
    pages = models.PositiveIntegerField(default=1)
    words = models.PositiveIntegerField(default=275)
    deadline = models.ForeignKey('pricing.DeadlineMultiplier', on_delete=models.SET_NULL, null=True, related_name='quotations')
    currency = models.ForeignKey('currencies.Currency', on_delete=models.SET_NULL, null=True, related_name='quotations')
    course_subject = models.CharField(max_length=200, blank=True)
    specifications = models.TextField(blank=True)

    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    exchange_rate_used = models.DecimalField(max_digits=12, decimal_places=6, default=1.00)
    pricing_season = models.ForeignKey('pricing.PricingSeason', on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    admin_notes = models.TextField(blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Q-{self.request_id} ({self.customer.email})"

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = uuid.uuid4().hex[:10].upper()
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        if not self.words and self.service:
            from pricing.models import PriceConfig
            config = PriceConfig.get_active()
            self.words = self.pages * config.words_per_page
        super().save(*args, **kwargs)


class QuotationAttachment(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=quotation_attachment_path)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename
