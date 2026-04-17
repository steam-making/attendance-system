import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import PhoneVerification
import json

User = get_user_model()

@csrf_exempt
def send_email_verification(request):
    """이메일로 인증번호 발송 (무료 이메일 인증)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'success': False, 'message': '이메일 주소를 입력해주세요.'})

        # ✅ 1인 1계정: 이메일 중복 체크
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': '이미 가입된 이메일입니다.'})

        # 6자리 랜덤 번호 생성
        code = str(random.randint(100000, 999999))
        
        # 기존 인증 내역 삭제 (새로운 인증 시도 시 기존 것 무효화)
        PhoneVerification.objects.filter(email=email).delete()
        
        # 데이터베이스 저장
        PhoneVerification.objects.create(email=email, code=code)
        
        # 이메일 발송
        subject = "[출첵마스터] 회원가입 인증번호 안내"
        message = f"안녕하세요. 출첵마스터입니다.\n\n회원가입 인증번호는 [{code}] 입니다.\n5분 이내에 입력해 주세요."
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@medutech.kr')
        
        try:
            send_mail(subject, message, from_email, [email])
            print(f"[{email}] 인증번호 발송 완료: {code} (터미널 확인용)")
        except Exception as mail_err:
            # 메일 발송 실패 시 (설정 미비 등) 터미널에 출력하여 개발 편의 제공
            print(f"!!!!!!!! EMAIL SEND ERROR: {mail_err}")
            print(f"[{email}] 인증번호 (메일발송실패): {code}")
            # 실제 운영 환경이라면 에러를 반환하겠지만, 테스트를 위해 일단 성공 응답
        
        return JsonResponse({
            'success': True, 
            'message': '인증 메일이 발송되었습니다. (받은편지함 또는 스팸함을 확인해 주세요)'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def confirm_verification_code(request):
    """입력된 인증번호 확인 (이메일 및 휴대폰 공용)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        phone = data.get('phone')
        code = data.get('code')

        if email:
            verification = PhoneVerification.objects.filter(email=email, code=code).last()
        elif phone:
            verification = PhoneVerification.objects.filter(phone=phone, code=code).last()
        else:
            return JsonResponse({'success': False, 'message': '인증 대상 정보가 없습니다.'})
        
        if not verification:
            return JsonResponse({'success': False, 'message': '인증번호가 일치하지 않습니다.'})
        
        if verification.is_expired():
            return JsonResponse({'success': False, 'message': '인증번호가 만료되었습니다. 다시 시도해주세요.'})

        # 인증 완료 처리
        verification.is_verified = True
        verification.save()

        # 세션에 인증 완료 정보 저장 (회원가입 폼 제출 시 최종 확인용)
        if email:
            verified_email = email.strip().lower()
            request.session['verified_email'] = verified_email
            request.session.modified = True  # ✅ 세션 변경 명시
        
        if phone:
            verified_phone = phone.strip()
            request.session['verified_phone'] = verified_phone
            request.session.modified = True

        return JsonResponse({'success': True, 'message': '인증되었습니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
