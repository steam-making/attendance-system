from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
import uuid

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        소셜 로그인 시 이미 다른 방식(일반 가입 등)으로 가입된 이메일이 있다면
        자동으로 계정을 연결해주는 로직
        """
        user = sociallogin.user
        if user.id:
            return
        if not user.email:
            return
            
        User = get_user_model()
        try:
            # 기존에 동일한 이메일로 가입한 유저가 있는지 확인
            existing_user = User.objects.get(email=user.email)
            # 있다면 해당 유저와 소셜 계정을 연결
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass

    def populate_user(self, request, sociallogin, data):
        """
        가입 시 사용자 이름을 자동으로 생성 (중복 방지)
        """
        user = super().populate_user(request, sociallogin, data)
        
        # 만약 username이 비어있거나 중복될 가능성이 있다면 고유하게 변경
        User = get_user_model()
        if not user.username or User.objects.filter(username=user.username).exists():
            # 이메일 앞부분 + 무작위 문자열로 고유 ID 생성
            email_prefix = user.email.split('@')[0] if user.email else "user"
            user.username = f"{email_prefix}_{uuid.uuid4().hex[:4]}"
            
        return user
