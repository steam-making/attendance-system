from rest_framework import serializers
from .models import Student, Attendance

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'grade', 'classroom', 'number', 'name', 'phone']

class AttendanceSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'program', 'date']
