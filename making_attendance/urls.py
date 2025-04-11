"""
URL configuration for making_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('login', permanent=False)),  # 👉 기본 접속은 로그인으로
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # accounts 앱 URL 포함
    path('accounts/', include('django.contrib.auth.urls')),  # 로그인/로그아웃 URL 추가
    path('attendance/', include('attendance.urls')),  # ✅ 출결 체크 연결
]  
