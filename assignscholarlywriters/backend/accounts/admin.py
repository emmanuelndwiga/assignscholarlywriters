from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_customer', 'is_staff', 'date_joined')
    list_filter = ('is_customer', 'is_staff', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    fieldsets = UserAdmin.fieldsets + (
        ('Additional', {'fields': ('phone', 'is_customer')}),
    )
