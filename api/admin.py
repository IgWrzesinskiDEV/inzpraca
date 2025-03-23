from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, GodzinyPracy, WniosekUrlopowy

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'dzial', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Dodatkowe informacje', {'fields': ('role', 'dzial')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dodatkowe informacje', {'fields': ('role', 'dzial')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(GodzinyPracy)
admin.site.register(WniosekUrlopowy)