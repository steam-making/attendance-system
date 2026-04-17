import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend

class UnverifiedEmailBackend(SMTPBackend):
    """
    포트 587(TLS)에서 인증서 검증 오류(CERTIFICATE_VERIFY_FAILED)를 무시하기 위한 커스텀 백엔드
    """
    def open(self):
        if self.connection:
            return False
        try:
            # SSL 컨텍스트 생성 시 검증 건너뛰기 설정
            context = ssl._create_unverified_context()
            
            # SMTP 객체 생성 (부모 클래스의 속성 직접 참조)
            self.connection = self.connection_class(
                self.host, self.port, 
                timeout=self.timeout
            )
            
            if self.use_tls:
                self.connection.starttls(context=context)
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False
