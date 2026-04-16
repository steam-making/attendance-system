from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PaymentLog

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # 목록 화면에서 보일 필드들
    list_display = ['username', 'email', 'membership_tier', 'subscription_end_date', 'is_staff']
    
    # 상세 수정 화면 구성
    fieldsets = UserAdmin.fieldsets + (
        ("멤버십 및 구독 정보", {
            'fields': ('membership_tier', 'subscription_end_date', 'customer_uid'),
        }),
        ("추가 정보", {
            'fields': ('phone',),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'merchant_uid', 'amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'merchant_uid']