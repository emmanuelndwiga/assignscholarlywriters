from django.db import models


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)  # USD, GBP, CAD, AUD
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)
    is_base = models.BooleanField(default=False, help_text='Only one currency can be the base')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} ({self.symbol})"


class ExchangeRate(models.Model):
    base_currency = models.CharField(max_length=3, default='GBP')
    target_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=12, decimal_places=6)
    fetched_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    api_source = models.CharField(max_length=100, default='exchangerate-api')

    class Meta:
        ordering = ['-fetched_at']
        verbose_name_plural = 'Exchange Rates'

    def __str__(self):
        return f"1 {self.base_currency} = {self.rate} {self.target_currency}"

    @classmethod
    def get_latest_rate(cls, base, target):
        if base == target:
            return 1.0
        from django.utils import timezone
        rate = cls.objects.filter(
            base_currency=base,
            target_currency=target,
            expires_at__gt=timezone.now()
        ).order_by('-fetched_at').first()
        return float(rate.rate) if rate else None
