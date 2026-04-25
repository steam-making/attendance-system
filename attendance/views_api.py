from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
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
@permission_classes([IsAuthenticated])
def attendance_today_list(request):
    """
    오늘의 출석 명단 조회 및 초기화 (웹/앱 공용)
    결과를 현재 로그인한 강사님의 학교 데이터로 한정합니다.
    """
    today = timezone.localdate()
    my_schools = request.user.schools.all()

    # 1. 학교 ID 파악
    if request.method == 'POST':
        school_id = request.data.get('school_id')
    else:
        school_id = request.query_params.get('school_id')

    # 2. 학교 ID가 없으면 현재 활성 세션에서 찾음 (내 학교 중에서만)
    if not school_id:
        active_session = AttendanceSession.objects.filter(
            school__in=my_schools, 
            date=today, 
            is_active=True
        ).order_by('-started_at').first()
        if active_session:
            school_id = active_session.school_id

    # 3. 그럼에도 없으면 에러 (보안 및 성능을 위해 전체 조회를 막음)
    if not school_id:
        return Response({
            "ok": False, 
            "error": "school_id is required. Please select a school first."
        }, status=status.HTTP_400_BAD_REQUEST)

    # 4. 내 소유의 학교 학생들만 필터링 (아이디별/장소별 격리 핵심)
    students = Student.objects.filter(school_id=school_id, school__user=request.user)
    
    # 해당 학교가 내 소유가 아닐 경우 빈 리스트 또는 에러 처리
    if not students.exists() and not my_schools.filter(id=school_id).exists():
        return Response({
            "ok": False, 
            "error": "You do not have permission for this school."
        }, status=status.HTTP_403_FORBIDDEN)

    attendance = Attendance.objects.filter(date=today, student__in=students)
    att_map = {a.student_id: a for a in attendance}

    # POST 요청 시 명단이 비어있으면 '대기' 상태로 자동 생성 (수업 시작 로직과 연동)
    if request.method == 'POST':
        with transaction.atomic():
            for s in students:
                if s.id not in att_map:
                    Attendance.objects.create(student=s, status='대기', date=today)
            # 생성 후 다시 조회
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
    """서버 상태 확인용"""
    return Response({"ok": True, "status": "ok"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def students_today(request):
    """
    내 학교의 학생 목록 + 오늘 출석상태 (앱 화면용)
    결과를 철저히 로그인 유저 및 선택 장소로 한정합니다.
    """
    today = timezone.localdate()
    school_id = request.query_params.get('school_id')

    # 내 학생들만 필터링
    students = Student.objects.filter(school__user=request.user)
    if school_id:
        students = students.filter(school_id=school_id)
    else:
        # 학교 ID가 지정되지 않으면 빈 리스트를 반환하여 서버 부하 및 보안 노출 방지
        return Response({
            "ok": True, 
            "data": {"date": str(today), "items": []}
        }, status=status.HTTP_200_OK)

    today_att = Attendance.objects.filter(date=today, student__in=students)
    att_map = {a.student_id: a for a in today_att}

    items = []
    for s in students:
        a = att_map.get(s.id)
        items.append({
            "student_id": s.id,
            "name": getattr(s, "name", ""),
            "phone": getattr(s, "phone", ""),
            "department": getattr(s, "department", None),
            "grade": getattr(s, "grade", None),
            "class_no": getattr(s, "class_no", None), #classroom일 수 있음
            "number": getattr(s, "number", None),
            "today_status": getattr(a, "status", "none") if a else "none",
            "attendance_id": a.id if a else None,
        })

    return Response({"ok": True, "data": {"date": str(today), "items": items}}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def attendance_check_api(request):
    """
    출석 처리 (앱 전용)
    본인 소유의 학생에 대해서만 처리가 가능하도록 검증합니다.
    """
    student_id = request.data.get("student_id")
    if not student_id:
        return Response({"ok": False, "error": "student_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 내 소유의 학생인지 확인 (보안 검증)
        student = Student.objects.get(id=student_id, school__user=request.user)
    except Student.DoesNotExist:
        return Response({"ok": False, "error": "Student not found or access denied"}, status=status.HTTP_403_FORBIDDEN)

    status_map = {
        "present": "출석", "late": "지각", "absence": "결석", "absent": "결석",
        "waiting": "대기", "cancel": "취소", "canceled": "취소", "ended": "종료처리",
    }
    raw_status = request.data.get("status", "출석")
    normalized_status = status_map.get(raw_status, raw_status)

    user_settings, _ = Setting.objects.get_or_create(user=request.user)
    today = timezone.localdate()

    obj, created = Attendance.objects.get_or_create(
        student_id=student_id,
        date=today,
        defaults={"status": normalized_status}
    )
    if not created:
        obj.status = normalized_status
        obj.save()

    send_sms = False
    sms_message = ""

    # 등급 및 설정에 따른 문자 발송 로직
    if normalized_status == "출석":
        if user_settings.send_attendance_sms:
            sms_message = resolve_and_render_message(student.school, "출석", student.name, user_settings)
            send_sms = True
        else: normalized_status = "출석(문자x)"
    elif normalized_status == "지각":
        if user_settings.send_lateness_sms:
            sms_message = resolve_and_render_message(student.school, "지각", student.name, user_settings)
            send_sms = True
        else: normalized_status = "지각(문자x)"
    elif normalized_status == "결석":
        if user_settings.send_absence_sms:
            sms_message = resolve_and_render_message(student.school, "결석", student.name, user_settings)
            send_sms = True
        else: normalized_status = "결석(문자x)"
    elif normalized_status == "취소":
        if user_settings.send_cancel_sms:
            sms_message = resolve_and_render_message(student.school, "취소", student.name, user_settings)
            send_sms = True
        else: normalized_status = "취소(문자x)"
    elif normalized_status == "종료처리":
        if user_settings.send_class_end_sms:
            sms_message = resolve_and_render_message(student.school, "종료처리", student.name, user_settings)
            send_sms = True
        else: normalized_status = "종료처리(문자x)"

    if obj.status != normalized_status:
        obj.status = normalized_status
        obj.save(update_fields=['status'])

    return Response({
        "ok": True,
        "created": created,
        "attendance_id": obj.id,
        "status": obj.status,
        "send_sms": send_sms,
        "sms_message": sms_message,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def attendance_end_api(request):
    """
    수업 종료 처리 (앱 전용)
    본인 소유의 학생에 대해서만 처리가 가능합니다.
    """
    student_id = request.data.get("student_id")
    if not student_id:
        return Response({"ok": False, "error": "student_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        student = Student.objects.get(id=student_id, school__user=request.user)
    except Student.DoesNotExist:
        return Response({"ok": False, "error": "Student not found or access denied"}, status=status.HTTP_403_FORBIDDEN)

    today = timezone.localdate()
    obj, created = Attendance.objects.get_or_create(
        student_id=student_id,
        date=today,
        defaults={"status": "종료처리"}
    )
    if not created:
        obj.status = "종료처리"
        obj.save()

    user_settings, _ = Setting.objects.get_or_create(user=request.user)

    status_to_save = "종료처리"
    send_sms = False
    sms_message = ""

    if user_settings.send_class_end_sms:
        sms_message = resolve_and_render_message(student.school, "종료처리", student.name, user_settings)
        send_sms = True
    else: status_to_save = "종료처리(문자x)"

    obj.status = status_to_save
    obj.save(update_fields=['status'])

    return Response({
        "ok": True,
        "created": created,
        "attendance_id": obj.id,
        "status": obj.status,
        "send_sms": send_sms,
        "sms_message": sms_message,
    }, status=status.HTTP_200_OK)
