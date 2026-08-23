from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer', 'service', 'academic_level', 'pages', 'total_amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'academic_level', 'service')
    search_fields = ('order_id', 'customer__name', 'customer__email')
    readonly_fields = ('order_id', 'created_at', 'updated_at')
