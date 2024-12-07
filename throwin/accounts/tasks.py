from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from store.management.commands.base_store import japanese_stores
import random


# def send_mail_task(subject, message, to_email):
#     send_mail(
#         subject=subject,
#         message=message,
#         from_email=settings.EMAIL_HOST_USER,
#         recipient_list=[to_email],
#         fail_silently=False,
#     )


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
def print_something():
    print("Hello, world!")
