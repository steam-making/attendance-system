from django.db import migrations, models


OLD_DEFAULTS = {
    "attendance_message": "{student_name} 학생 출석하였습니다.",
    "lateness_message": "{student_name} 학생 지각하였습니다.",
    "absence_message": "{student_name} 학생 결석하였습니다.",
    "class_end_message": "{student_name} 학생 수업 종료되었습니다.",
    "cancel_message": "{student_name} 학생 출석이 취소되었습니다.",
}

NEW_DEFAULTS = {
    "attendance_message": "{program_name}에 {student_name} 학생이 출석하였습니다.",
    "lateness_message": "{program_name}에 {student_name} 학생이 지각하였습니다.",
    "absence_message": "{program_name}에 {student_name} 학생이 결석하였습니다.",
    "class_end_message": "{program_name}에 {student_name} 학생의 수업이 종료되었습니다.",
    "cancel_message": "{program_name}에 {student_name} 학생의 출석이 취소되었습니다.",
}


def forward_update_messages(apps, schema_editor):
    Setting = apps.get_model("attendance", "Setting")
    for field_name, old_message in OLD_DEFAULTS.items():
        Setting.objects.filter(**{field_name: old_message}).update(**{field_name: NEW_DEFAULTS[field_name]})


def backward_update_messages(apps, schema_editor):
    Setting = apps.get_model("attendance", "Setting")
    for field_name, new_message in NEW_DEFAULTS.items():
        Setting.objects.filter(**{field_name: new_message}).update(**{field_name: OLD_DEFAULTS[field_name]})


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0010_school_absence_message_override_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="setting",
            name="attendance_message",
            field=models.TextField(default="{program_name}에 {student_name} 학생이 출석하였습니다.", verbose_name="출석 시 문자 메시지"),
        ),
        migrations.AlterField(
            model_name="setting",
            name="lateness_message",
            field=models.TextField(default="{program_name}에 {student_name} 학생이 지각하였습니다.", verbose_name="지각 시 문자 메시지"),
        ),
        migrations.AlterField(
            model_name="setting",
            name="absence_message",
            field=models.TextField(default="{program_name}에 {student_name} 학생이 결석하였습니다.", verbose_name="결석 시 문자 메시지"),
        ),
        migrations.AlterField(
            model_name="setting",
            name="class_end_message",
            field=models.TextField(default="{program_name}에 {student_name} 학생의 수업이 종료되었습니다.", verbose_name="종료 시 문자 메시지"),
        ),
        migrations.AlterField(
            model_name="setting",
            name="cancel_message",
            field=models.TextField(default="{program_name}에 {student_name} 학생의 출석이 취소되었습니다.", verbose_name="취소 시 문자 메시지"),
        ),
        migrations.RunPython(forward_update_messages, backward_update_messages),
    ]
