from datetime import timedelta

from celery import shared_task

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from accounts.models import TemporaryUser


@shared_task()
def send_mail_task(subject, message, to_email):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[to_email],
        fail_silently=False,
    )


@shared_task()
def delete_old_temporary_users():
    """
        task to delete old temporary users records older than 48 hours
    """
    threshold_time = timezone.now() - timedelta(hours=48)

    old_users = TemporaryUser.objects.filter(created_at__lt=threshold_time)
    deleted_cont, _ = old_users.delete()

    return f"{deleted_cont} temporary users deleted"


@shared_task()
def print_something():
    print("Hello, world!")
