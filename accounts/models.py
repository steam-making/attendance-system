from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):  # ✅ 사용자 모델 확장
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username