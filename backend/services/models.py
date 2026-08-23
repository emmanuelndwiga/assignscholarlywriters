from django.db import models


class AcademicLevel(models.Model):
    name = models.CharField(max_length=100)  # e.g. High School, Undergraduate, Masters, PhD
    slug = models.SlugField(unique=True)
    multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Academic Levels'

    def __str__(self):
        return self.name


class ServiceType(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    base_price_per_page = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Service Types'

    def __str__(self):
        return self.name
