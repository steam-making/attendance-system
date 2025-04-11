from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm

EMAIL_DOMAINS = [
    ('naver.com', 'naver.com'),
    ('gmail.com', 'gmail.com'),
    ('hanmail.net', 'hanmail.net'),
    ('nate.com', 'nate.com'),
    ('직접입력', '직접입력'),
]

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(label="이름", max_length=30, required=True)
    email_id = forms.CharField(label="이메일 아이디", max_length=100, required=True)
    email_domain = forms.ChoiceField(label="이메일 도메인", choices=EMAIL_DOMAINS, required=True)
    email_custom = forms.CharField(label="직접입력 도메인", required=False)
    phone = forms.CharField(label="전화번호", max_length=20)

    class Meta:
        model = get_user_model()  # CustomUser 모델 사용 시
        fields = ['username', 'first_name', 'password1', 'password2','email_id', 'email_domain', 'email_custom', 'phone',]
        labels = {
            'username': '아이디',
            'first_name': '이름',
            'phone': '전화번호',
            'email': '이메일',
            'password1': '비밀번호',
            'password2': '비밀번호 확인',
        }

    def clean(self):
        cleaned_data = super().clean()
        domain = cleaned_data.get('email_domain')
        email_id = cleaned_data.get('email_id')
        email_custom = cleaned_data.get('email_custom')

        if domain == '직접입력':
            full_email = f"{email_id}@{email_custom}"
        else:
            full_email = f"{email_id}@{domain}"

        cleaned_data['email'] = full_email  # User 모델의 email 필드에 연결

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        user.phone = self.cleaned_data.get('phone')
        user.first_name = self.cleaned_data.get('first_name')
        
        #user.full_clean()  # 👈 이 줄이 구체적인 유효성 검사 에러를 발생시켜줌 (개발 중에만 사용!)
        
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(label="이메일", required=True)

    class Meta:
        model = get_user_model() 
        fields = ['username', 'email']
        
class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="현재 비밀번호", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(label="새 비밀번호", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(label="새 비밀번호 확인", widget=forms.PasswordInput(attrs={'class': 'form-control'}))