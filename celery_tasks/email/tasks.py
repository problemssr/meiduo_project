from django.core.mail import send_mail

from celery_tasks.main import app
from meiduo_mall import settings


@app.task(bind=True)
def send_active_email(self, email, verify_url):
    # 发送激活邮件
    subject = '主题'
    message = "内容"
    from_email = settings.EMAIL_FROM
    # 有格式的内容
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
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
