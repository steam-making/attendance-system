from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class CustomUser(AbstractUser):  # ✅ 사용자 모델 확장
    phone = models.CharField(max_length=20, blank=True, null=True)

    # 회원 등급 필드
    TIER_CHOICES = [
        ('FREE', 'Free (광고 노출)'),
        ('PRO', 'Pro (광고 제거/자동화)'),
    ]
    membership_tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='FREE', verbose_name="회원 등급")
    subscription_end_date = models.DateField(null=True, blank=True, verbose_name="구독 종료일")
    customer_uid = models.CharField(max_length=100, null=True, blank=True, verbose_name="정기결제 빌링키")

    @property
    def is_pro(self):
        """현재 유저가 유효한 Pro 등급인지 확인"""
        if self.membership_tier == 'PRO':
            # 구독 종료일이 설정되어 있다면 오늘 날짜와 비교
            if self.subscription_end_date:
                return self.subscription_end_date >= timezone.localdate()
            return True
        return False

    @property
    def school_limit(self):
        """등급별 생성 가능한 최대 학교 수"""
        return 5 if self.is_pro else 1

    @property
    def student_limit_per_school(self):
        """학교당 최대 학생 수 (전 등급 80명)"""
        return 80

    @property
    def can_use_automation(self):
        """자동화 기능(지각/종료 문자) 사용 가능 여부"""
        return self.is_pro

    def __str__(self):
        return f"{self.username} ({self.membership_tier})"

class PaymentLog(models.Model):  # ✅ 결제 이력 모델 추가
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_logs')
    merchant_uid = models.CharField(max_length=100, unique=True, verbose_name="주문번호")
    imp_uid = models.CharField(max_length=100, null=True, blank=True, verbose_name="포트원 번호")
    amount = models.PositiveIntegerField(verbose_name="결제금액")
    status = models.CharField(max_length=20, default='ready', verbose_name="결제상태")  # ready, paid, cancelled, failed
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="결제일시")

    class Meta:
        verbose_name = "결제 로그"
        verbose_name_plural = "결제 로그 목록"

    def __str__(self):
        return f"{self.user.username} - {self.merchant_uid} ({self.amount}원)"

class PhoneVerification(models.Model):  # ✅ 범용 인증용 모델로 사용
    phone = models.CharField(max_length=20, verbose_name="휴대폰 번호", null=True, blank=True)
    email = models.EmailField(verbose_name="이메일", null=True, blank=True)  # ✅ 이메일 추가
    code = models.CharField(max_length=6, verbose_name="인증 코드")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시각")
    is_verified = models.BooleanField(default=False, verbose_name="인증 여부")

    class Meta:
        verbose_name = "인증 코드"
        verbose_name_plural = "인증 코드 목록"

    def is_expired(self):
        # 5분 유효
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    def __str__(self):
        return f"{self.phone} - {self.code} ({'인증됨' if self.is_verified else '미인증'})"