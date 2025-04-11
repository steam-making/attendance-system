from django.contrib import admin
from .models import Student, Attendance
from django.contrib import admin
from .models import School, Student

admin.site.register(School)

# Register your models here.

# ✅ 학생 정보에 필터/정렬 기능 추가
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'grade', 'classroom', 'number', 'phone']
    list_filter = ['department', 'grade', 'classroom']
    
# (선택) 출석 정보도 admin에 등록
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date']
    list_filter = ['date']
    search_fields = ['student__name']