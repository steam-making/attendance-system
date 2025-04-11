from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Student, Attendance
from .serializers import StudentSerializer, AttendanceSerializer
from django.utils import timezone

@api_view(['GET'])
def student_list(request):
    students = Student.objects.all()
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def attendance_today_list(request):
    today = timezone.now().date()
    attendance = Attendance.objects.filter(date=today)
    serializer = AttendanceSerializer(attendance, many=True)
    return Response(serializer.data)
