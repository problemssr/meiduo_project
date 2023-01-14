from django.core.mail import send_mail

from celery_tasks.main import app
from meiduo_mall import settings


@app.task(bind=True)
def send_active_email(self, email):
    # 发送激活邮件
    subject = '主题'
    message = "内容"
    from_email = settings.EMAIL_FROM
    html_message = '<h1>哈哈哈哈和</h1>'
    recipient_list = [email]
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message
        )
    except Exception as e:
        self.retry(exc=e)
