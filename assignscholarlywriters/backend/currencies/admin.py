from django.contrib import admin
from .models import Currency, ExchangeRate


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'is_base', 'is_active')
    list_filter = ('is_active', 'is_base')


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('base_currency', 'target_currency', 'rate', 'fetched_at', 'expires_at')
    list_filter = ('base_currency', 'target_currency')
    readonly_fields = ('fetched_at',)
