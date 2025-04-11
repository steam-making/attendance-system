from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ("추가 정보", {'fields': ('phone',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)