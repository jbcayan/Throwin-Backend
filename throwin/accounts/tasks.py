from django.core.mail import send_mail
from django.conf import settings


def send_mail_task(subject, message, to_email):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[to_email],
        fail_silently=False,
    )