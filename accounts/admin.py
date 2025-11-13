from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # Show these fields in the admin form
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('user_type', 'code', 'phone')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('user_type', 'code', 'phone')}),
    )

    # Display fields in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'user_type', 'is_staff', 'is_superuser')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')

admin.site.register(CustomUser, CustomUserAdmin)
