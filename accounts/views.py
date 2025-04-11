from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .forms import UserUpdateForm, CustomPasswordChangeForm
from django.contrib.auth import get_user_model
from django.http import JsonResponse

def check_username(request):
    username = request.GET.get("username", None)
    exists = get_user_model().objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

@login_required
def profile(request):
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "회원 정보가 성공적으로 수정되었습니다.")
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        print(form.save())
        if form.is_valid():
            user = form.save()
            login(request, user)  # 회원가입 후 자동 로그인
            messages.success(request, f"환영합니다, {user.username}님! 회원가입이 완료되었습니다.")  # ✅ 환영 메시지 추가
            return redirect('select_school')  # 가입 후 홈페이지로 이동
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