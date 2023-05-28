from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, JWTToken


class JWTTokenInline(admin.StackedInline):
    model = JWTToken
    can_delete = False
    verbose_name_plural = 'Tokens'


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('bio', 'role')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('bio', 'role')}),
    )
    inlines = (JWTTokenInline,)


admin.site.register(User, UserAdmin)
