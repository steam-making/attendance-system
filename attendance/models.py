from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class School(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    program_name = models.CharField(max_length=100, help_text="운영 프로그램명 (예:로봇과학반)")
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
        ('출석', '출석'),
        ('지각', '지각'),
        ('결석', '결석'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='출석')  # ✅ 추가
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ 출석 시간

    def __str__(self):
        return f"{self.student} - {self.date}"
