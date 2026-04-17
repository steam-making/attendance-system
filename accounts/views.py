from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .forms import UserUpdateForm, CustomPasswordChangeForm
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib.auth.views import LoginView
from attendance.models import Setting
from attendance.forms import SettingsForm

User = get_user_model()

def check_username_duplicate(request):
    username = request.GET.get('username')
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

class CustomLoginView(LoginView):
    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')
        
        if remember_me:
            # 2주 동안 유지
            self.request.session.set_expiry(60 * 60 * 24 * 14)  
        else:
            # 브라우저 닫을 때 세션 만료 (기본값)
            self.request.session.set_expiry(0)
            
        return super().form_valid(form)

def check_username(request):
    username = request.GET.get("username", None)
    exists = get_user_model().objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

@login_required
def profile(request):
    from .models import PaymentLog
    from django.utils import timezone
    from datetime import timedelta
    
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "회원 정보가 성공적으로 수정되었습니다.")
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)

    # 최근 결제 내역 5개 가져오기
    payment_logs = PaymentLog.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # 🔹 각 결제 건별로 7일 이내 환불 가능 여부 계산
    limit_date = timezone.now() - timedelta(days=7)
    for log in payment_logs:
        log.is_refundable = log.created_at >= limit_date

    context = {
        'form': form,
        'payment_logs': payment_logs,
    }

    return render(request, 'accounts/profile.html', context)

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        
        # ✅ 이메일 인증 여부 최종 확인
        email_id = request.POST.get('email_id')
        domain = request.POST.get('email_domain')
        email_custom = request.POST.get('email_custom')
        
        if domain == '직접입력':
            current_email = f"{email_id}@{email_custom}".strip().lower()
        else:
            current_email = f"{email_id}@{domain}".strip().lower()
            
        verified_email = request.session.get('verified_email')
        
        if current_email != verified_email:
            messages.error(request, "이메일 인증이 필요하거나 이메일 주소가 변경되었습니다. 다시 인증해 주세요.")
            return render(request, 'accounts/signup.html', {'form': form})

        if form.is_valid():
            user = form.save()
            
            # 가입 완료 후 세션에서 인증 정보 삭제
            if 'verified_email' in request.session:
                del request.session['verified_email']
                
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')  # 회원가입 후 자동 로그인
            messages.success(request, f"환영합니다, {user.username}님! 회원가입이 완료되었습니다.")
            return redirect('select_school')
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def change_password(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # 비밀번호 변경 후 자동 로그인 유지
            messages.success(request, "비밀번호가 성공적으로 변경되었습니다.")
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def settings_view(request):
    settings, created = Setting.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = SettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "설정이 성공적으로 저장되었습니다.")
            return redirect('settings')
    else:
        form = SettingsForm(instance=settings)

    return render(request, 'accounts/settings.html', {'form': form})
