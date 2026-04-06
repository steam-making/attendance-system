from django.db import migrations, models
from django.db.models import Count, Max


def deduplicate_attendance_records(apps, schema_editor):
    Attendance = apps.get_model('attendance', 'Attendance')
    duplicates = (
        Attendance.objects.values('student_id', 'date')
        .annotate(keep_id=Max('id'), total=Count('id'))
        .filter(total__gt=1)
    )

    for duplicate in duplicates:
        Attendance.objects.filter(
            student_id=duplicate['student_id'],
            date=duplicate['date']
        ).exclude(id=duplicate['keep_id']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0012_attendance_absence_reason'),
    ]

    operations = [
        migrations.RunPython(deduplicate_attendance_records, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='attendance',
            constraint=models.UniqueConstraint(fields=('student', 'date'), name='uniq_attendance_student_date'),
        ),
    ]
