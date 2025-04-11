from django.urls import path
from . import views, views_api
from .views import upload_students_excel
from .views import delete_selected_students
from .views import select_school, register_school, update_school, delete_school


urlpatterns = [
    # 출석 리스트 페이지 (웹용)
    path('', views.select_school, name='select_school'),
    
    path('list/', views.attendance_list, name='attendance_list'),

    # 출석 처리 API (앱에서 사용) ✅ JSON 응답!
    path('ajax/check/<int:student_id>/', views.ajax_attendance_check, name='ajax_attendance_check'),

    # 출석 취소용 API (옵션)
    path('ajax/cancel/<int:student_id>/', views.ajax_attendance_cancel, name='ajax_attendance_cancel'),

    # 학생 등록 (웹용)
    path('student/create/', views.student_create, name='student_create'),

    # 학생 수정 (웹용)
    path('student/update/<int:student_id>/', views.student_update, name='student_update'),
    
    # 오늘 출석
    path('api/attendance/today/', views_api.attendance_today_list, name='attendance_today'),
    
    # 엑셀 업로드
    path('students/upload/', upload_students_excel, name='upload_students_excel'),
    
    # 학생 삭제
    path('students/delete_selected/', delete_selected_students, name='delete_selected_students'),
    path('student/delete/<int:pk>/', views.delete_student, name='delete_student'),
    # 학교 등록
    path('schools/register/', register_school, name='register_school'),
    # 학교 수정 
    path('school/<int:pk>/update/', update_school, name='update_school'),
    path('student/move/<int:pk>/', views.move_student_department, name='move_student_department'),
    # 학교 삭제
    path('school/<int:pk>/delete/', delete_school, name='delete_school'),
    
    path('select_school/', select_school, name='select_school'),
    path('register_school/', register_school, name='register_school'),

]
