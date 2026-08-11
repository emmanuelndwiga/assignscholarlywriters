# cases/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Category, CaseReport, Attachment, CaseUpdate, CaseAuditLog
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'case_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)

    def case_count(self, obj):
        return obj.cases.count()
    case_count.short_description = 'Number of cases'


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ('uploaded_at',)
    fields = ('file', 'original_filename', 'content_type', 'size', 'uploaded_at')
    can_delete = True


class CaseUpdateInline(admin.TabularInline):
    model = CaseUpdate
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('author_type', 'author_user', 'message', 'visibility', 'is_read_by_victim', 'created_at')
    can_delete = True
    autocomplete_fields = ('author_user',)


@admin.register(CaseReport)
class CaseReportAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number', 'category', 'status', 'assigned_handler',
        'created_at', 'updated_at', 'tracking_code_link'
    )
    list_filter = (
        'status', 'category', 'platform', 'relationship_to_perpetrator',
        'assigned_handler', 'created_at'
    )
    search_fields = (
        'reference_number', 'description', 'perpetrator_name',
        'perpetrator_username', 'contact_value'
    )
    readonly_fields = (
        'reference_number', 'tracking_code_hash', 'created_at', 'updated_at'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Identification', {
            'fields': ('reference_number', 'tracking_code_hash', 'category')
        }),
        ('Incident Details', {
            'fields': ('description', 'date_of_incident', 'approximate_time',
                       'platform', 'platform_other', 'location_context')
        }),
        ('Perpetrator Information', {
            'fields': ('relationship_to_perpetrator', 'perpetrator_name',
                       'perpetrator_username', 'perpetrator_profile_url',
                       'perpetrator_contact', 'perpetrator_additional_info')
        }),
        ('Contact for Updates', {
            'fields': ('contact_method', 'contact_value')
        }),
        ('Case Handling', {
            'fields': ('assigned_handler', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [AttachmentInline, CaseUpdateInline]

    actions = ['mark_as_under_review', 'mark_as_resolved', 'mark_as_closed']

    def tracking_code_link(self, obj):
        # You can't recover the original code, but you can show the hash preview
        return format_html(
            '<span style="font-family: monospace;">{}</span>',
            obj.tracking_code_hash[:20] + '…'
        )
    tracking_code_link.short_description = 'Tracking code (hash)'

    def mark_as_under_review(self, request, queryset):
        updated = queryset.update(status=CaseReport.Status.UNDER_REVIEW)
        self.message_user(request, f'{updated} case(s) marked as Under Review.')
    mark_as_under_review.short_description = 'Mark selected as Under Review'

    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status=CaseReport.Status.RESOLVED)
        self.message_user(request, f'{updated} case(s) marked as Resolved.')
    mark_as_resolved.short_description = 'Mark selected as Resolved'

    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status=CaseReport.Status.CLOSED)
        self.message_user(request, f'{updated} case(s) marked as Closed.')
    mark_as_closed.short_description = 'Mark selected as Closed'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'case', 'content_type', 'size', 'uploaded_at')
    list_filter = ('content_type', 'uploaded_at')
    search_fields = ('original_filename', 'case__reference_number')
    readonly_fields = ('uploaded_at',)
    ordering = ('-uploaded_at',)


@admin.register(CaseUpdate)
class CaseUpdateAdmin(admin.ModelAdmin):
    list_display = ('case', 'author_type', 'author_user', 'visibility', 'is_read_by_victim', 'created_at')
    list_filter = ('author_type', 'visibility', 'is_read_by_victim', 'created_at')
    search_fields = ('case__reference_number', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    autocomplete_fields = ('author_user',)


@admin.register(CaseAuditLog)
class CaseAuditLogAdmin(admin.ModelAdmin):
    list_display = ('case', 'action', 'actor', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('case__reference_number', 'action', 'detail')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    autocomplete_fields = ('actor',)