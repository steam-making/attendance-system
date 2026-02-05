from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import Attendance, AttendanceSession, Setting, Student


def _weekday_label(target_date):
    labels = ['월', '화', '수', '목', '금', '토', '일']
    return labels[target_date.weekday()]


def _parse_time(value):
    if not value:
        return None
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


def _time_matches(now, target_time):
    return now.hour == target_time.hour and now.minute == target_time.minute


class Command(BaseCommand):
    help = "Automatically update lateness/end attendance based on schedule."

    def handle(self, *args, **options):
        now = timezone.localtime()
        today = now.date()
        tz = timezone.get_current_timezone()

        sessions = AttendanceSession.objects.filter(date=today, is_active=True)
        if not sessions.exists():
            self.stdout.write(f"[{now:%H:%M}] skip: no active sessions")
            return

        for session in sessions.select_related('school'):
            school = session.school
            if session.started_at and now < session.started_at:
                self.stdout.write(f"[{now:%H:%M}] skip: {school.name} session not started")
                continue

            school = session.school
            class_days = []
            if school.class_days:
                class_days = [day.strip() for day in school.class_days.split(',') if day.strip()]
            if class_days and _weekday_label(today) not in class_days:
                self.stdout.write(f"[{now:%H:%M}] skip: {school.name} not class day")
                continue

            settings, _ = Setting.objects.get_or_create(user=school.user)
            department_times = school.department_times or {}
            processed_any = False

            for department, time_info in department_times.items():
                if not time_info:
                    continue
                start_time = _parse_time(time_info.get('start'))
                end_time = _parse_time(time_info.get('end'))
                if not start_time or not end_time:
                    continue

                start_dt = timezone.make_aware(datetime.combine(today, start_time), tz)
                end_dt = timezone.make_aware(datetime.combine(today, end_time), tz)
                lateness_dt = start_dt + timedelta(minutes=10)

                if settings.auto_send_lateness_sms and _time_matches(now, lateness_dt.time()):
                    students = Student.objects.filter(school=school, department=department)
                    student_ids = list(students.values_list('id', flat=True))
                    if student_ids:
                        existing_qs = Attendance.objects.filter(date=today, student_id__in=student_ids)
                        existing_ids = set(existing_qs.values_list('student_id', flat=True))
                        updated_count = existing_qs.filter(status__in=['대기', '취소']).update(status='지각')
                        missing_ids = [student_id for student_id in student_ids if student_id not in existing_ids]
                        Attendance.objects.bulk_create(
                            [Attendance(student_id=student_id, date=today, status='지각') for student_id in missing_ids]
                        )
                        processed_any = True
                        self.stdout.write(
                            f"[{now:%H:%M}] 지각 처리: {school.name} {department} updated={updated_count} created={len(missing_ids)}"
                        )

                if settings.auto_send_class_end_sms and _time_matches(now, end_dt.time()):
                    ended_count = Attendance.objects.filter(
                        date=today,
                        student__school=school,
                        student__department=department,
                        status='출석'
                    ).update(status='종료처리')
                    processed_any = True
                    self.stdout.write(
                        f"[{now:%H:%M}] 종료 처리: {school.name} {department} ended={ended_count}"
                    )

            if not processed_any:
                self.stdout.write(f"[{now:%H:%M}] no actions: {school.name}")
