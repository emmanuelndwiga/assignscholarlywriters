from django.contrib import admin
from .models import PricingSeason, DeadlineMultiplier, PriceConfig, AuditLog


@admin.register(PricingSeason)
class PricingSeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'season_type', 'start_date', 'end_date', 'global_multiplier', 'is_active')
    list_filter = ('season_type', 'is_active')
    search_fields = ('name',)


@admin.register(DeadlineMultiplier)
class DeadlineMultiplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'days', 'multiplier', 'order', 'is_active')
    list_filter = ('is_active',)
    ordering = ['days']


@admin.register(PriceConfig)
class PriceConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'words_per_page', 'base_currency', 'is_active', 'updated_at')
    list_filter = ('is_active',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'model_name', 'object_id', 'performed_by', 'timestamp')
    list_filter = ('action', 'model_name')
    search_fields = ('description', 'object_id')
    readonly_fields = ('action', 'model_name', 'object_id', 'description', 'old_value', 'new_value', 'performed_by', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
