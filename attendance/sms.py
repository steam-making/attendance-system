from attendance.models import Setting


MESSAGE_FIELD_BY_STATUS = {
    "출석": "attendance_message",
    "지각": "lateness_message",
    "결석": "absence_message",
    "종료처리": "class_end_message",
    "취소": "cancel_message",
}

OVERRIDE_FIELD_BY_MESSAGE_FIELD = {
    "attendance_message": "attendance_message_override",
    "lateness_message": "lateness_message_override",
    "absence_message": "absence_message_override",
    "class_end_message": "class_end_message_override",
    "cancel_message": "cancel_message_override",
}


def default_message_map(settings_obj):
    return {
        "attendance_message": settings_obj.attendance_message,
        "lateness_message": settings_obj.lateness_message,
        "absence_message": settings_obj.absence_message,
        "class_end_message": settings_obj.class_end_message,
        "cancel_message": settings_obj.cancel_message,
    }


def get_effective_message_template(school, settings_obj, message_field):
    override_field = OVERRIDE_FIELD_BY_MESSAGE_FIELD[message_field]
    override_value = getattr(school, override_field)
    if override_value is not None and override_value.strip() != "":
        return override_value
    return getattr(settings_obj, message_field)


def get_effective_message_for_status(school, settings_obj, status):
    message_field = MESSAGE_FIELD_BY_STATUS.get(status)
    if not message_field:
        return ""
    return get_effective_message_template(school, settings_obj, message_field)


def render_message(template, student_name="", school_name="", program_name=""):
    rendered = template or ""
    context = {
        "{student_name}": student_name,
        "{school_name}": school_name,
        "{program_name}": program_name,
    }
    for key, value in context.items():
        rendered = rendered.replace(key, value or "")
    return rendered


def resolve_and_render_message(school, status, student_name="", settings_obj=None):
    settings_obj = settings_obj or Setting.objects.get_or_create(user=school.user)[0]
    template = get_effective_message_for_status(school, settings_obj, status)
    return render_message(template, student_name=student_name, school_name=school.name, program_name=school.program_name)
