import json
import os
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import PaymentLog

def get_portone_token():
    """포트원 REST API 사용을 위한 액세스 토큰 발급"""
    api_key = os.getenv("PORTONE_API_KEY")
    api_secret = os.getenv("PORTONE_API_SECRET")
    
    url = "https://api.iamport.kr/users/getToken"
    payload = {
        "imp_key": api_key,
        "imp_secret": api_secret
    }
    
    try:
        response = requests.post(url, json=payload)
        response_data = response.json()
        if response_data.get("code") == 0:
            return response_data.get("response").get("access_token")
    except Exception as e:
        print(f"Token error: {e}")
    return None

def schedule_next_payment(user, amount):
    """포트원 API를 사용하여 30일 뒤 정기 결제 예약"""
    token = get_portone_token()
    
    # 🔹 [테스트 모드 체크] 공용 테스트 ID 사용 시 우회
    is_test_shop = os.getenv("PORTONE_SHOP_ID") in ["imp31012345", "imp10391932"]
    
    if not token:
        if is_test_shop:
            print("정기 결제 예약: 테스트 모드 - 예약 성공으로 간주")
            return True
        print("정기 결제 예약 실패: 토큰 발급 불가")
        return False
    
    # 다음 결제 예정일 (30일 뒤)
    next_run_at = int((timezone.now() + timedelta(days=30)).timestamp())
    merchant_uid = f"AUTO-{user.id}-{int(timezone.now().timestamp())}"
    
    url = "https://api.iamport.kr/subscribe/payments/schedule"
    headers = {"Authorization": token}
    payload = {
        "customer_uid": user.customer_uid,
        "schedules": [
            {
                "merchant_uid": merchant_uid,
                "schedule_at": next_run_at,
                "amount": amount,
                "name": "출첵마스터 Pro 정기 구독 (자동연장)",
                "buyer_email": user.email,
                "buyer_name": user.username
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        print(f"정기 결제 예약 결과: {res_data}")
        return res_data.get("code") == 0
    except Exception as e:
        print(f"정기 결제 예약 오류: {e}")
        return False

@login_required
def payment_unsubscribe_api(request):
    """정기 결제 해지 (다음 결제부터 중단)"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    user = request.user
    if not user.customer_uid:
        return JsonResponse({'status': 'error', 'message': '등록된 정기 결제 정보가 없습니다.'}, status=400)

    # 1. 포트원 토큰 획득
    token = get_portone_token()
    if not token:
        return JsonResponse({'status': 'error', 'message': '서버 통신 오류 (Token).'}, status=500)

    # 2. 포트원 예약 취소 API 호출
    url = "https://api.iamport.kr/subscribe/payments/unschedule"
    headers = {"Authorization": token}
    payload = {"customer_uid": user.customer_uid}

    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        
        # 🔹 [테스트 모드 체크] 공용 테스트 ID 사용 시 우회
        is_test_shop = os.getenv("PORTONE_SHOP_ID") in ["imp31012345", "imp10391932"]

        if res_data.get("code") == 0 or is_test_shop:
            # 성공 시 유저의 customer_uid 삭제 (더 이상 예약 안함)
            user.customer_uid = None
            user.save()
            return JsonResponse({
                'status': 'success', 
                'message': '정기 구독 해지가 완료되었습니다. 다음 결제일부터는 결제되지 않습니다. (현재 Pro 혜택은 만료일까지 유지됩니다.)'
            })
        else:
            return JsonResponse({'status': 'error', 'message': res_data.get("message", "해지 처리 중 오류가 발생했습니다.")}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'서버 오류: {str(e)}'}, status=500)

@login_required
def payment_cancel_api(request):
    """일반 결제 취소 및 환불 (등급 즉시 회수)"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        merchant_uid = data.get('merchant_uid')
        
        # 해당 결제 로그 찾기
        payment = PaymentLog.objects.filter(user=request.user, merchant_uid=merchant_uid, status='paid').first()
        if not payment:
            return JsonResponse({'status': 'error', 'message': '취소 가능한 결제 내역을 찾을 수 없습니다.'}, status=404)

        # 🔹 [보안] 7일 이내인지 검증
        limit_date = timezone.now() - timedelta(days=7)
        if payment.created_at < limit_date:
            return JsonResponse({'status': 'error', 'message': '결제 후 7일이 경과하여 직접 취소가 불가능합니다. 고객센터로 문의해주세요.'}, status=400)

        # 1. 포트원 토큰 획득
        token = get_portone_token()
        
        # 🔹 [테스트 모드 체크]
        is_test_shop = os.getenv("PORTONE_SHOP_ID") in ["imp31012345", "imp10391932"]

        if not token and not is_test_shop:
            return JsonResponse({'status': 'error', 'message': '서버 통신 오류 (Token).'}, status=500)

        # 2. 포트원 환불 API 호출
        url = "https://api.iamport.kr/payments/cancel"
        headers = {"Authorization": token}
        payload = {
            "merchant_uid": merchant_uid,
            "reason": "사용자 요청에 의한 취소"
        }

        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()

        if res_data.get("code") == 0 or is_test_shop:
            # 취소 성공 시 처리
            payment.status = 'cancelled'
            payment.save()
            
            # 유저 등급 즉시 FREE로 변경 및 종료일 초기화
            user = request.user
            user.membership_tier = 'FREE'
            user.subscription_end_date = None
            user.customer_uid = None  # 정기구독 정보도 삭제
            user.save()
            
            return JsonResponse({'status': 'success', 'message': '결제 취소 및 환불 처리가 완료되었습니다.'})
        else:
            return JsonResponse({'status': 'error', 'message': res_data.get("message", "환불 처리 중 오류가 발생했습니다.")}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'서버 오류: {str(e)}'}, status=500)

def process_payment_success(user, merchant_uid, imp_uid, amount, days=30, customer_uid=None):
    """결제 검증 성공 시 유저 등급 업데이트 및 로그 기록 (공용 로직)"""
    user.membership_tier = 'PRO'
    
    # 🔹 전달받은 days(30, 180, 420 등)만큼 기간 연장
    base_date = user.subscription_end_date if user.is_pro and user.subscription_end_date else timezone.localdate()
    user.subscription_end_date = base_date + timedelta(days=int(days))
    
    # 정기 결제라면 빌링키 저장 및 다음 결제 예약
    if customer_uid:
        user.customer_uid = customer_uid
        # 빌링키가 처음 등록되었거나 갱신된 경우 다음 결제 예약 실행
        schedule_next_payment(user, amount)
        
    user.save()

    # 결제 로그 기록
    PaymentLog.objects.create(
        user=user,
        merchant_uid=merchant_uid,
        imp_uid=imp_uid,
        amount=amount,
        status='paid'
    )

    return JsonResponse({
        'status': 'success',
        'message': '결제가 성공적으로 확인되었습니다. 이제 Pro 기능을 사용하실 수 있습니다!',
        'subscription_end_date': user.subscription_end_date.strftime('%Y-%m-%d')
    })

@login_required
def payment_verify_api(request):
    """결제 완료 후 서버 측 유효성 검증 API"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        imp_uid = data.get('imp_uid')
        merchant_uid = data.get('merchant_uid')
        amount = data.get('amount')
        days = data.get('days', 30)  # 🔹 기본값 30일
        customer_uid = data.get('customer_uid') # 🔹 정기 결제 시 전달됨
        
        if not imp_uid or not merchant_uid:
            if not customer_uid: # 정기결제 빌링키 발급 시에는 imp_uid가 없을 수 있음 (포트원 v1 기준)
                return JsonResponse({'status': 'error', 'message': '필수 결제 정보가 누락되었습니다.'}, status=400)

        # 1. 포트원 토큰 획득
        token = get_portone_token()
        
        # 🔹 [테스트 모드 체크] 공용 테스트 ID 사용 시 실제 검증 우회
        is_test_shop = os.getenv("PORTONE_SHOP_ID") in ["imp31012345", "imp10391932"]
        
        if not token:
            if is_test_shop:
                return process_payment_success(request.user, merchant_uid, imp_uid, amount, days, customer_uid)
            return JsonResponse({'status': 'error', 'message': '결제 서버 통신 오류 (Token).'}, status=500)

        # 2. 포트원 서버에서 결제 정보 조회
        # 빌링키 발급건(정기결제)은 imp_uid가 없을 수 있으므로 체크
        if imp_uid:
            url = f"https://api.iamport.kr/payments/{imp_uid}"
            headers = {"Authorization": token}
            response = requests.get(url, headers=headers)
            res_data = response.json()

            if res_data.get("code") != 0:
                if is_test_shop:
                    return process_payment_success(request.user, merchant_uid, imp_uid, amount, days, customer_uid)
                return JsonResponse({'status': 'error', 'message': '결제 정보를 찾을 수 없습니다.'}, status=404)

            payment_data = res_data.get("response")
            paid_amount = payment_data.get("amount")
            paid_status = payment_data.get("status")

            # 3. 결제 금액 및 상태 검증
            if paid_status == 'paid' and str(paid_amount) == str(amount):
                return process_payment_success(request.user, merchant_uid, imp_uid, amount, days, customer_uid)
        else:
            # 빌링키 발급만 된 경우 (0원 결제 혹은 최초 빌링키 요청)
            if customer_uid:
                return process_payment_success(request.user, merchant_uid, imp_uid, amount, days, customer_uid)

        # 검증 실패 시 로그 기록
        PaymentLog.objects.create(
            user=request.user,
            merchant_uid=merchant_uid,
            imp_uid=imp_uid,
            amount=amount,
            status='failed'
        )
        return JsonResponse({'status': 'error', 'message': '결제 검증에 실패하였습니다.'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'서버 오류: {str(e)}'}, status=500)
