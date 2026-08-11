# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, StaffInvitation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the User model."""
    
    # Fields to display in the list view
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'role', 'phone_number', 'is_staff', 'is_active'
    )
    
    # Filters in the sidebar
    list_filter = (
        'role', 'is_staff', 'is_active', 'is_superuser',
        'date_joined'
    )
    
    # Search fields
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    
    # Ordering
    ordering = ('-date_joined',)
    
    # Add role and phone_number to the fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number'),
        }),
    )
    
    # Fields shown when adding a new user
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number'),
        }),
    )


@admin.register(StaffInvitation)
class StaffInvitationAdmin(admin.ModelAdmin):
    """Admin for staff invitations."""
    
    list_display = (
        'email', 'role', 'invited_by', 'created_at',
        'expires_at', 'accepted_status', 'token_preview'
    )
    
    list_filter = ('role', 'accepted_at', 'created_at', 'expires_at')
    
    search_fields = ('email', 'invited_by__email', 'invited_by__username', 'token')
    
    readonly_fields = ('token', 'created_at', 'accepted_at')
    
    fieldsets = (
        (None, {
            'fields': ('email', 'role', 'invited_by')
        }),
        ('Token & Expiry', {
            'fields': ('token', 'expires_at', 'accepted_at', 'created_at'),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ('-created_at',)
    
    def accepted_status(self, obj):
        """Display a coloured badge showing if the invitation was accepted."""
        if obj.accepted_at:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Accepted</span>'
            )
        elif obj.is_valid():
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ Pending</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Expired</span>'
            )
    accepted_status.short_description = 'Status'
    
    def token_preview(self, obj):
        """Show a shortened version of the token for quick reference."""
        return obj.token[:12] + '…' if obj.token else ''
    token_preview.short_description = 'Token (truncated)'
    
    # Actions
    actions = ['resend_invitation']
    
    def resend_invitation(self, request, queryset):
        """Action to resend invitations (placeholder – you can implement email logic)."""
        count = queryset.count()
        # Placeholder: you could trigger email sending here
        self.message_user(
            request,
            f'Resend logic would be triggered for {count} invitation(s).',
            level='INFO'
        )
    resend_invitation.short_description = 'Resend selected invitations'