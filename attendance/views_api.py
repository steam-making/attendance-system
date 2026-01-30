from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from .models import Student, Attendance
from .serializers import AttendanceSerializer

@api_view(['GET'])
def attendance_today_list(request):
    today = timezone.localdate()
    attendance = Attendance.objects.filter(date=today)
    serializer = AttendanceSerializer(attendance, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"ok": True, "status": "ok"}, status=status.HTTP_200_OK)


@api_view(['GET'])
def students_today(request):
    """
    학생 목록 + 오늘 출석상태 (앱 화면용)
    """
    today = timezone.localdate()
    today_att = Attendance.objects.filter(date=today)
    att_map = {a.student_id: a for a in today_att}

    items = []
    for s in Student.objects.all():
        a = att_map.get(s.id)
        items.append({
            "student_id": s.id,
            "name": getattr(s, "name", ""),
            "phone": getattr(s, "phone", ""),
            "department": getattr(s, "department", None),
            "grade": getattr(s, "grade", None),
            "class_no": getattr(s, "class_no", None),
            "number": getattr(s, "number", None),
            "today_status": getattr(a, "status", "none") if a else "none",
            "attendance_id": a.id if a else None,
        })

    return Response({"ok": True, "data": {"date": str(today), "items": items}}, status=status.HTTP_200_OK)


@api_view(['POST'])
@transaction.atomic
def attendance_check_api(request):
    """
    출석 처리 (앱 POST)
    body: {"student_id": 1}
    """
    student_id = request.data.get("student_id")
    if not student_id:
        return Response({"ok": False, "error": "student_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    today = timezone.localdate()
    obj, created = Attendance.objects.get_or_create(
        student_id=student_id,
        date=today,
        defaults={"status": "present"}
    )
    if not created:
        obj.status = "present"
        obj.save()

    return Response({"ok": True, "created": created, "attendance_id": obj.id, "status": obj.status}, status=status.HTTP_200_OK)


@api_view(['POST'])
@transaction.atomic
def attendance_end_api(request):
    """
    수업 종료 처리 (앱 POST)
    body: {"student_id": 1}
    """
    student_id = request.data.get("student_id")
    if not student_id:
        return Response({"ok": False, "error": "student_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    today = timezone.localdate()
    obj, created = Attendance.objects.get_or_create(
        student_id=student_id,
        date=today,
        defaults={"status": "ended"}
    )
    if not created:
        obj.status = "ended"
        obj.save()

    return Response({"ok": True, "created": created, "attendance_id": obj.id, "status": obj.status}, status=status.HTTP_200_OK)
