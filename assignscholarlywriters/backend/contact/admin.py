from django.contrib import admin
from .models import ContactMessage, ContactAttachment


class ContactAttachmentInline(admin.TabularInline):
    model = ContactAttachment
    extra = 0
    readonly_fields = ('original_filename', 'uploaded_at')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'service', 'created_at')
    list_filter = ('service', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)
    inlines = [ContactAttachmentInline]
