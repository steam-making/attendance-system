from django.urls import path
from . import views, views_api
from .views import (
    upload_students_excel,
    delete_selected_students,
    select_school, register_school, update_school, delete_school
)

urlpatterns = [
    # =========================
    # ✅ API (앱 표준)
    # =========================
    path('api/health/', views_api.health, name='api_health'),
    path('api/students/today/', views_api.students_today, name='api_students_today'),
    path('api/attendance/check/', views_api.attendance_check_api, name='api_attendance_check'),
    path('api/attendance/end/', views_api.attendance_end_api, name='api_attendance_end'),

    path('api/attendance/today/', views_api.attendance_today_list, name='attendance_today'),
    path('api/attendance/today/<int:student_id>/update/', views.update_today_attendance_status, name='update_today_attendance_status'),

    # =========================
    # ✅ 웹 페이지
    # =========================
    path('', views.select_school, name='select_school'),              # 기본 진입
    path('list/', views.attendance_list, name='attendance_list'),

    # =========================
    # ✅ AJAX (웹에서 출석/취소/종료)
    # =========================
    path('ajax/check/<int:student_id>/', views.ajax_attendance_check, name='ajax_attendance_check'),
    path('ajax/cancel/<int:student_id>/', views.ajax_attendance_cancel, name='ajax_attendance_cancel'),
    path('ajax/end/<int:student_id>/', views.mark_attendance_end, name='ajax_attendance_end'),

    # =========================
    # ✅ 학생
    # =========================
    path('student/create/', views.student_create, name='student_create'),
    path('student/update/<int:pk>/', views.student_update, name='student_update'),
    path('student/delete/<int:pk>/', views.delete_student, name='delete_student'),
    path('student/move/<int:pk>/', views.move_student_department, name='move_student_department'),

    path('students/delete_selected/', delete_selected_students, name='delete_selected_students'),
    path('students/upload/', upload_students_excel, name='upload_students_excel'),

    # =========================
    # ✅ 학교
    # =========================
    path('schools/register/', register_school, name='register_school'),
    path('school/<int:pk>/update/', update_school, name='update_school'),
    path('school/<int:pk>/delete/', delete_school, name='delete_school'),
]
