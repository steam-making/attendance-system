from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from .sms import resolve_and_render_message
from django.views.decorators.csrf import csrf_exempt
from .models import Student, Attendance, Setting, AttendanceSession
from .serializers import AttendanceSerializer

@csrf_exempt
@api_view(['GET', 'POST'])
def attendance_today_list(request):
    today = timezone.localdate()
    if request.method == 'POST' and not request.user.is_authenticated:
        return Response({"ok": False, "error": "authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    if request.method == 'POST':
        school_id = request.data.get('school_id')
    else:
        school_id = request.query_params.get('school_id')

    if not school_id:
        active_session = AttendanceSession.objects.filter(date=today, is_active=True).order_by('-started_at').first()
        if active_session:
            school_id = active_session.school_id

    if request.method == 'POST' and not school_id:
        return Response({"ok": False, "error": "school_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    students = Student.objects.all()
    if school_id:
        students = students.filter(school_id=school_id)

    attendance = Attendance.objects.filter(date=today, student__in=students)
    att_map = {a.student_id: a for a in attendance}

    if request.method == 'POST':
        for s in students:
            if s.id not in att_map:
                Attendance.objects.create(student=s, status='대기', date=today)
        attendance = Attendance.objects.filter(date=today, student__in=students)
        att_map = {a.student_id: a for a in attendance}

    items = []
    for s in students:
        a = att_map.get(s.id)
        items.append({
            "id": a.id if a else None,
            "student": {
                "id": s.id,
                "grade": s.grade,
                "classroom": s.classroom,
                "number": s.number,
                "name": s.name,
                "phone": s.phone,
            },
            "program": a.program if a else None,
            "date": str(a.date) if a else str(today),
            "status": a.status if a else "대기",
        })

    return Response(items)

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

    status_map = {
        "present": "출석",
        "late": "지각",
        "absence": "결석",
        "absent": "결석",
        "waiting": "대기",
        "cancel": "취소",
        "canceled": "취소",
        "ended": "종료처리",
    }
    raw_status = request.data.get("status", "출석")
    normalized_status = status_map.get(raw_status, raw_status)

    student = Student.objects.get(id=student_id)
    user_settings, _ = Setting.objects.get_or_create(user=student.school.user)

    today = timezone.localdate()
    obj, created = Attendance.objects.get_or_create(
        student_id=student_id,
        date=today,
        defaults={"status": normalized_status}
    )
    if not created:
        obj.status = normalized_status
        obj.save()
    else:
        # If it was created with a status that might have changed to (문자x)
        # we need to ensure the saved status is the normalized/modified one.
        obj.status = normalized_status
        obj.save()
    student = Student.objects.get(id=student_id)
    user_settings, _ = Setting.objects.get_or_create(user=student.school.user)

    send_sms = False
    sms_message = ""

    if normalized_status == "출석":
        if user_settings.send_attendance_sms:
            sms_message = resolve_and_render_message(student.school, "출석", student.name, user_settings)
            send_sms = True
        else:
            normalized_status = "출석(문자x)"
    elif normalized_status == "지각":
        if user_settings.send_lateness_sms:
            sms_message = resolve_and_render_message(student.school, "지각", student.name, user_settings)
            send_sms = True
        else:
            normalized_status = "지각(문자x)"
    elif normalized_status == "결석":
        if user_settings.send_absence_sms:
            sms_message = resolve_and_render_message(student.school, "결석", student.name, user_settings)
            send_sms = True
        else:
            normalized_status = "결석(문자x)"
    elif normalized_status == "취소":
        if user_settings.send_cancel_sms:
            sms_message = resolve_and_render_message(student.school, "취소", student.name, user_settings)
            send_sms = True
        else:
            normalized_status = "취소(문자x)"
    elif normalized_status == "종료처리":
        if user_settings.send_class_end_sms:
            sms_message = resolve_and_render_message(student.school, "종료처리", student.name, user_settings)
            send_sms = True
        else:
            normalized_status = "종료처리(문자x)"

    # Final save to ensure (문자x) is in the DB if needed
    if obj.status != normalized_status:
        obj.status = normalized_status
        obj.save(update_fields=['status'])

    return Response(
        {
            "ok": True,
            "created": created,
            "attendance_id": obj.id,
            "status": obj.status,
            "send_sms": send_sms,
            "sms_message": sms_message,
        },
        status=status.HTTP_200_OK
    )


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
        defaults={"status": "종료처리"}
    )
    if not created:
        obj.status = "종료처리"
        obj.save()

    student = Student.objects.get(id=student_id)
    user_settings, _ = Setting.objects.get_or_create(user=student.school.user)

    status_to_save = "종료처리"
    send_sms = False
    sms_message = ""

    if user_settings.send_class_end_sms:
        sms_message = resolve_and_render_message(student.school, "종료처리", student.name, user_settings)
        send_sms = True
    else:
        status_to_save = "종료처리(문자x)"

    obj.status = status_to_save
    obj.save(update_fields=['status'])

    return Response(
        {
            "ok": True,
            "created": created,
            "attendance_id": obj.id,
            "status": obj.status,
            "send_sms": send_sms,
            "sms_message": sms_message,
        },
        status=status.HTTP_200_OK
    )
