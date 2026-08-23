from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'order', 'paypal_order_id', 'amount', 'currency', 'status', 'paid_at', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('payment_id', 'paypal_order_id', 'paypal_transaction_id')
    readonly_fields = ('payment_id', 'raw_response', 'created_at', 'updated_at')
