from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class School(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    program_name = models.CharField(max_length=100, help_text="운영 프로그램명 (예:로봇과학반)")

    # 수업 요일 (콤마로 구분하여 저장: 월,화,수,목,금,토,일)
    class_days = models.CharField(
        max_length=20,
        blank=True,
        help_text="수업 요일을 선택하세요 (예: 월,화,수,목,금)"
    )

    # 부서 (콤마로 구분하여 저장: 1부,2부,3부,미수강)
    departments = models.CharField(
        max_length=30,
        blank=True,
        help_text="운영하는 부서를 선택하세요 (예: 1부,2부,3부)"
    )

    # 부서 시간 (JSON 형식으로 저장: {"1부": {"start": "09:00", "end": "12:00"}, ...})
    department_times = models.JSONField(
        blank=True,
        null=True,
        help_text="각 부서별 수업 시간을 입력하세요"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Student(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)  # ✅ 추가
    department = models.CharField(
        max_length=10,
        choices=[
            ('1부', '1부'),
            ('2부', '2부'),
            ('3부', '3부'),
        ],
        default='1부'  # ✅ 여기 추가!
    )
    grade = models.IntegerField(verbose_name="학년")
    classroom = models.IntegerField(verbose_name="반")
    number = models.IntegerField(verbose_name="번호")
    name = models.CharField(max_length=50, verbose_name="이름")
    phone = models.CharField(max_length=20, verbose_name="휴대폰 번호")

    def __str__(self):
        return f"{self.department} {self.grade}-{self.classroom} {self.number}번 {self.name}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('대기', '대기'),
        ('출석', '출석'),
        ('지각', '지각'),
        ('결석', '결석'),
        ('취소', '취소'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='출석')  # ✅ 추가
    program = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ 출석 시간

    def __str__(self):
        return f"{self.student} - {self.date}"

class Setting(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # SMS message templates
    attendance_message = models.TextField(default="{student_name} 학생 출석하였습니다.", verbose_name="출석 시 문자 메시지")
    lateness_message = models.TextField(default="{student_name} 학생 지각하였습니다.", verbose_name="지각 시 문자 메시지")
    absence_message = models.TextField(default="{student_name} 학생 결석하였습니다.", verbose_name="결석 시 문자 메시지")
    class_end_message = models.TextField(default="{student_name} 학생 수업 종료되었습니다.", verbose_name="종료 시 문자 메시지")
    cancel_message = models.TextField(default="{student_name} 학생 출석이 취소되었습니다.", verbose_name="취소 시 문자 메시지")

    # Automation toggles
    auto_send_class_end_sms = models.BooleanField(default=False, verbose_name="자동 종료 문자 보내기")
    auto_send_lateness_sms = models.BooleanField(default=False, verbose_name="자동 지각 문자 보내기")

    def __str__(self):
        return f"{self.user.username}의 설정"
