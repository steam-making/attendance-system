from django.shortcuts import render, get_object_or_404, redirect
from .models import Student, Attendance
from django.utils import timezone
from django.contrib import messages
from .forms import StudentForm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
import openpyxl
from collections import defaultdict, OrderedDict
from .forms import SchoolForm
from django.contrib.auth.decorators import login_required
from attendance.models import School

color_map_header = {
    "1부": "table-primary",
    "2부": "table-success",
    "3부": "table-warning",
    "4부": "table-info",
    "5부": "table-light",
}

school_colors = [
    "#e6f2ff",  # 연한 파랑
    "#e8f7e4",  # 연한 초록
    "#fff9e6",  # 연한 노랑
    "#f0f4ff",  # 연한 하늘
    "#f9f9f9",  # 연한 회색
]

@login_required
def update_school(request, pk):
    school = get_object_or_404(School, pk=pk, user=request.user)
    if request.method == 'POST':
        form = SchoolForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            return redirect('select_school')
    else:
        form = SchoolForm(instance=school)
    return render(request, 'attendance/register_school.html', {'form': form})

@login_required
def delete_school(request, pk):
    school = get_object_or_404(School, pk=pk, user=request.user)
    if request.method == 'POST':
        school.delete()
        return redirect('select_school')
    return HttpResponse("허용되지 않은 접근입니다.", status=405)

@login_required
def move_student_department(request, pk):
    student = get_object_or_404(Student, pk=pk, school__user=request.user)

    if request.method == 'POST':
        new_department = request.POST.get('department')
        if new_department:
            student.department = new_department
            student.save()
            messages.success(request, f"{student.name} 학생이 {new_department}로 이동되었습니다.")
        return redirect(f"/attendance/list/?school={student.school.id}")

    return HttpResponse("허용되지 않은 접근입니다.", status=405)


@login_required
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk, school__user=request.user)
    if request.method == 'POST':
        student.delete()
        return redirect(f"/attendance/list/?school={student.school.id}")
    return HttpResponse("허용되지 않은 접근입니다.", status=405)

@csrf_exempt
def delete_selected_students(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        student_ids = data.get('student_ids', [])
        Student.objects.filter(id__in=student_ids).delete()
        return JsonResponse({'status': 'success', 'deleted_count': len(student_ids)})

    return JsonResponse({'status': 'invalid_method'})

@login_required
def register_student(request):
    school_id = request.GET.get('school')  # ✅ URL에서 school ID 가져오기
    selected_school = School.objects.filter(id=school_id, user=request.user).first()

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.school = selected_school  # ✅ 자동으로 학교 지정
            student.save()
            return redirect(f'/attendance/?school={selected_school.id}')
    else:
        form = StudentForm()

    return render(request, 'attendance/register_student.html', {
        'form': form,
        'selected_school': selected_school
    })


@login_required
def select_school(request):
    user = request.user
    schools = School.objects.filter(user=user)

    color_list = ["#e6f2ff", "#e8f7e4", "#fff9e6", "#f0f4ff", "#f9f9f9"]
    school_colors = {}

    for i, school in enumerate(schools):
        school_colors[school.id] = color_list[i % len(color_list)]

    if request.method == 'POST':
        selected_id = request.POST.get('school')
        return redirect(f"/attendance/?school={selected_id}")

    return render(request, 'attendance/select_school.html', {
        'schools': schools,
        "school_colors": school_colors,
    })

@login_required
def register_school(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid():
            school = form.save(commit=False)
            school.user = request.user
            school.save()
            return redirect('select_school')
    else:
        form = SchoolForm()
    return render(request, 'attendance/register_school.html', {'form': form})

@login_required
def upload_students_excel(request):
    school_id = request.GET.get('school')
    selected_school = School.objects.filter(id=school_id, user=request.user).first()
    print(school_id)

    if not selected_school:
        return HttpResponse("유효한 학교 ID가 필요합니다.", status=400)

    if request.method == 'POST' and request.FILES.get('file'):
        excel_file = request.FILES['file']
        wb = openpyxl.load_workbook(excel_file)
        sheet = wb.active

        for row in sheet.iter_rows(min_row=2, values_only=True):
            department, grade, classroom, number, name, phone = row

            Student.objects.create(
                school=selected_school,
                department=department,
                grade=grade,
                classroom=classroom,
                number=number,
                name=name,
                phone=phone
            )

        messages.success(request, "학생 엑셀 업로드가 완료되었습니다.")
        return redirect(f"/attendance/?school={selected_school.id}")

    return render(request, 'attendance/upload_excel.html', {
        'selected_school': selected_school
    })


@csrf_exempt
def ajax_attendance_cancel(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id)
        today = timezone.now().date()
        Attendance.objects.filter(student=student, date=today).delete()
        return JsonResponse({'status': 'canceled', 'student': student.name})
    return JsonResponse({'status': 'invalid'})

@csrf_exempt
def ajax_attendance_check(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    today = timezone.now().date()

    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        print("📦 받은 데이터:", data)
        status = data.get('status', '출석')  # 기본값은 '출석'
        program = data.get('program_name')

        print(f"✅ 상태: {status}, 프로그램명: {program}")

        # 중복 확인
        already_checked = Attendance.objects.filter(student=student, date=today).exists()
        print(f"✅ 중복확인 : {already_checked}")
        if already_checked:
            return JsonResponse({'status': 'already_checked', 'student': student.name})

        attendance = Attendance.objects.create(student=student, status=status, program=program, status=status)
        print(f"✅ 오브젝트추가 : {attendance}")
        return JsonResponse({
            'status': 'success',
            'student': student.name,
            'phone': student.phone,
            'attendance_status': status,
            'program_name': program,
            'created_at': timezone.localtime(attendance.created_at).strftime('%H:%M:%S')  # ✅ 출석 시간 추가
        })

    return JsonResponse({'status': 'invalid_method'})


def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('attendance_list')  # 또는 적절한 페이지
    else:
        form = StudentForm(instance=student)

    return render(request, 'attendance/student_form.html', {
        'form': form,
        'student': student,
        'selected_school': student.school
        })

def student_create(request):
    school_id = request.GET.get('school')  # ✅ URL에서 school ID 가져오기
    selected_school = School.objects.filter(id=school_id, user=request.user).first()

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.school = selected_school  # ✅ 자동으로 학교 지정
            student.save()
            return redirect(f'/attendance/?school={selected_school.id}')
    else:
        form = StudentForm()

    return render(request, 'attendance/student_form.html', {
        'form': form,
        'selected_school': selected_school
    })
    
def attendance_list(request):
    user = request.user

    # ✅ 로그인 사용자의 학교 목록
    schools = School.objects.filter(user=user)

    # ✅ GET 파라미터에서 선택된 학교 ID 가져오기
    selected_school_id = request.GET.get('school')
    
    if selected_school_id:
        selected_school = School.objects.filter(id=selected_school_id, user=user).first()
    else:
        selected_school = schools.first()
    print(selected_school)
    # ✅ 선택된 학교에 해당하는 학생만 조회
    students = Student.objects.filter(school=selected_school) if selected_school else []
    
    today = timezone.now().date()
    attendances = {
        a.student.id: a for a in Attendance.objects.filter(date=today)
    }

    # ✅ 부서별로 묶되, 학년-반-번호로 정렬해서 넣기
    department_groups = defaultdict(list)
    for student in students:
        department_groups[student.department].append(student)

    for dept, student_list in department_groups.items():
        department_groups[dept] = sorted(
            student_list,
            key=lambda s: (s.grade, s.classroom, s.number)
        )
        
    # ✅ 부서 출력 순서 고정
    ordered_departments = OrderedDict()
    for dept in ['1부', '2부', '3부']:
        if dept in department_groups:
            ordered_departments[dept] = department_groups[dept]

    return render(request, 'attendance/attendance_list.html', {
        'departments': ordered_departments,
        'attendances': attendances,
        'schools': schools,                     # ✅ 이 부분 필수!
        'selected_school': selected_school,
        "color_map_header": color_map_header,
    })

def attendance_check(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    today = timezone.now().date()
    # 이미 출석한 학생이면 중복 방지
    already_checked = Attendance.objects.filter(student=student, date=today).exists()
    if not already_checked:
        Attendance.objects.create(student=student)
        messages.success(request, f"{student.name}님 출석 완료!")
        # 👉 여기에서 문자 보내는 로직이 나중에 들어갈 부분!
    else:
        messages.warning(request, f"{student.name}님은 이미 출석했습니다.")
    return redirect('attendance_list')
