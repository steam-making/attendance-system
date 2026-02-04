from django import forms
from .models import Student, Setting
from .models import School
from django import forms

class SchoolForm(forms.ModelForm):
    CLASS_DAY_CHOICES = [
        ('월', '월요일'),
        ('화', '화요일'),
        ('수', '수요일'),
        ('목', '목요일'),
        ('금', '금요일'),
        ('토', '토요일'),
        ('일', '일요일'),
    ]

    DEPARTMENT_CHOICES = [
        ('1부', '1부'),
        ('2부', '2부'),
        ('3부', '3부'),
        ('미수강', '미수강'),
    ]

    class_days = forms.MultipleChoiceField(
        choices=CLASS_DAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='수업 요일',
    )

    departments = forms.MultipleChoiceField(
        choices=DEPARTMENT_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='운영 부서',
    )

    first_class_start = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}), label='전체 시작 시간')
    break_time = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': '분'}), label='쉬는 시간 (분)')
    class_duration = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': '분'}), label='수업 시간 (분)')

    class Meta:
        model = School
        fields = ['name', 'program_name']
        labels = {
            'name': '학교 이름',
            'program_name': '프로그램명',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'program_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'program_name': '예: 로봇과학, 과학탐구 등',
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        class_days = self.cleaned_data.get('class_days', [])
        instance.class_days = ','.join(class_days) if class_days else ''

        departments = self.cleaned_data.get('departments', [])
        instance.departments = ','.join(departments) if departments else ''

        department_times = {}

        start = self.cleaned_data.get('first_class_start')
        break_time = self.cleaned_data.get('break_time')
        class_duration = self.cleaned_data.get('class_duration')

        if ({'1부', '2부', '3부'} & set(departments)) and start and break_time and class_duration:
            from datetime import datetime, timedelta, date

            if hasattr(start, 'hour'):
                start_time = datetime.combine(date.today(), start)
            else:
                try:
                    start_time = datetime.strptime(str(start), '%H:%M:%S')
                except ValueError:
                    start_time = datetime.strptime(str(start), '%H:%M')

            end_time = start_time + timedelta(minutes=class_duration)
            start_2부 = start_time + timedelta(minutes=class_duration + break_time)
            end_2부 = start_2부 + timedelta(minutes=class_duration)
            start_3부 = start_2부 + timedelta(minutes=class_duration + break_time)
            end_3부 = start_3부 + timedelta(minutes=class_duration)

            if '1부' in departments:
                department_times['1부'] = {
                    'start': start_time.strftime('%H:%M'),
                    'end': end_time.strftime('%H:%M')
                }

            if '2부' in departments:
                department_times['2부'] = {
                    'start': start_2부.strftime('%H:%M'),
                    'end': end_2부.strftime('%H:%M')
                }

            if '3부' in departments:
                department_times['3부'] = {
                    'start': start_3부.strftime('%H:%M'),
                    'end': end_3부.strftime('%H:%M')
                }

        instance.department_times = department_times if department_times else None

        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            if self.instance.class_days:
                self.initial['class_days'] = [
                    day.strip()
                    for day in self.instance.class_days.split(',')
                    if day.strip()
                ]
            if self.instance.departments:
                self.initial['departments'] = [
                    dept.strip()
                    for dept in self.instance.departments.split(',')
                    if dept.strip()
                ]

            department_times = self.instance.department_times or {}
            dept1 = department_times.get('1부')
            dept2 = department_times.get('2부')

            if dept1 and dept1.get('start'):
                self.initial['first_class_start'] = dept1.get('start')

            if dept1 and dept1.get('start') and dept1.get('end'):
                from datetime import datetime, timedelta

                start_1 = datetime.strptime(dept1['start'], '%H:%M')
                end_1 = datetime.strptime(dept1['end'], '%H:%M')
                duration_minutes = int((end_1 - start_1) / timedelta(minutes=1))
                if duration_minutes > 0:
                    self.initial['class_duration'] = duration_minutes

                if dept2 and dept2.get('start'):
                    start_2 = datetime.strptime(dept2['start'], '%H:%M')
                    break_minutes = int((start_2 - end_1) / timedelta(minutes=1))
                    if break_minutes > 0:
                        self.initial['break_time'] = break_minutes
        else:
            self.initial['departments'] = [choice[0] for choice in self.DEPARTMENT_CHOICES]


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['department', 'grade', 'classroom', 'number', 'name', 'phone']
        labels = {
            'department': '부서',
            'grade': '학년',
            'classroom': '반',
            'number': '번호',
            'name': '이름',
            'phone': '휴대폰 번호',
        }
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'grade': forms.NumberInput(attrs={'class': 'form-control'}),
            'classroom': forms.NumberInput(attrs={'class': 'form-control'}),
            'number': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = [
            'attendance_message',
            'lateness_message',
            'absence_message',
            'class_end_message',
            'cancel_message',
            'auto_send_class_end_sms',
            'auto_send_lateness_sms',
        ]
        widgets = {
            'attendance_message': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'}),
            'lateness_message': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'}),
            'absence_message': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'}),
            'class_end_message': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'}),
            'cancel_message': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'}),
            'auto_send_class_end_sms': forms.CheckboxInput(attrs={'class': 'rounded h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500'}),
            'auto_send_lateness_sms': forms.CheckboxInput(attrs={'class': 'rounded h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500'}),
        }
