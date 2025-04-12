from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import signup, profile, change_password, check_username
from .views import CustomLoginView

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('profile/', profile, name='profile'),  # 마이페이지 URL 추가
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),  # 로그인 뷰
    path('logout/', LogoutView.as_view(), name='logout'),  # 로그아웃 뷰
    path('change-password/', change_password, name='change_password'),  # 비밀번호 변경 페이지
    path('check-username/', check_username, name='check_username'), 
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
]
