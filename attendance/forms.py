from django import forms
from .models import Student
from .models import School
from django import forms

class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ['name', 'program_name']
        labels = {
            'name': '학교 이름',
            'program_name': '프로그램명',
        }
        help_texts = {
            'program_name': '예: 로봇과학, 과학탐구 등',
        }


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
