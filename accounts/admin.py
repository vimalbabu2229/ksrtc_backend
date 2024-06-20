from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model


class CustomUserAdmin(UserAdmin):
    """Define admin model for custom User model with no username field."""
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin', 
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ( 'date_created', 'last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_admin', 'is_superuser', 'is_staff'),
        }),
    )
    list_display = ('email', 'is_superuser', 'is_admin', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)


admin.site.register(get_user_model(), CustomUserAdmin)