from django.contrib import admin
from .models import Sample


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'level', 'pages', 'format', 'category', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'category', 'subject', 'level')
    search_fields = ('title', 'subject', 'description')
    list_editable = ('order', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'subject', 'level', 'pages', 'format', 'category')
        }),
        ('File', {
            'fields': ('file',)
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Settings', {
            'fields': ('order', 'is_active', 'created_at', 'updated_at')
        }),
    )
