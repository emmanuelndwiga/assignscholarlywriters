from django.db import models
from django.utils import timezone


class PricingSeason(models.Model):
    SEASON_TYPES = [
        ('normal', 'Normal'),
        ('november_peak', 'November Peak'),
        ('december_peak', 'December Peak'),
        ('january_peak', 'January Peak'),
        ('custom', 'Custom'),
    ]
    name = models.CharField(max_length=100)
    season_type = models.CharField(max_length=20, choices=SEASON_TYPES, default='normal')
    start_date = models.DateField()
    end_date = models.DateField()
    global_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.00,
        help_text='Applied to all prices during this season')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

    @classmethod
    def get_current(cls):
        today = timezone.now().date()
        return cls.objects.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).first()


class DeadlineMultiplier(models.Model):
    name = models.CharField(max_length=100)  # e.g. "14 days", "7 days"
    days = models.IntegerField(help_text='Number of days until deadline')
    multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['days']
        verbose_name_plural = 'Deadline Multipliers'

    def __str__(self):
        return f"{self.name} (x{self.multiplier})"


class PriceConfig(models.Model):
    """Master price configuration. Only one should be active at a time."""
    name = models.CharField(max_length=100, default='Default')
    words_per_page = models.IntegerField(default=275)
    base_currency = models.CharField(max_length=3, default='GBP')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Price Configurations'

    def __str__(self):
        return f"{self.name} ({self.base_currency})"

    @classmethod
    def get_active(cls):
        config = cls.objects.filter(is_active=True).first()
        if not config:
            config = cls.objects.create(name='Default')
        return config


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('price_change', 'Price Change'),
        ('season_change', 'Season Change'),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    performed_by = models.CharField(max_length=150, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.timestamp})"
