from django.contrib import admin
from .models import Quotation, QuotationAttachment


class QuotationAttachmentInline(admin.TabularInline):
    model = QuotationAttachment
    extra = 0
    readonly_fields = ('original_filename', 'uploaded_at')


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'customer', 'service', 'academic_level', 'pages', 'deadline', 'estimated_price', 'currency', 'status', 'created_at')
    list_filter = ('status', 'academic_level', 'service')
    search_fields = ('request_id', 'customer__name', 'customer__email', 'course_subject')
    readonly_fields = ('request_id', 'base_price', 'exchange_rate_used', 'created_at', 'updated_at')
    inlines = [QuotationAttachmentInline]


@admin.register(QuotationAttachment)
class QuotationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'original_filename', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
