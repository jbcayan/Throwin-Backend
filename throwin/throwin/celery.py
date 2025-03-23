from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from decouple import config

TIME_ZONE = config("TIME_ZONE")

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "throwin.settings")

app = Celery("throwin")

# Configure Celery with Django settings (namespace is 'CELERY')
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatically discover tasks in all registered Django app configs
app.autodiscover_tasks()

# Celery configuration with Redis as the broker and result backend
app.conf.update(
    broker_url="redis://redis_cache:6379",  # Broker URL for Redis
    result_backend="redis://redis_cache:6379",  # Result backend for Redis
    task_serializer="json",  # Task serialization format
    accept_content=["json"],  # Accept only JSON content for tasks
    result_serializer="json",  # Result serialization format
    timezone=TIME_ZONE,  # Set the timezone for Celery tasks
)

# Deleting old temporary users
app.conf.beat_schedule = {
    "delete-old-temporary-users-every-day": {
        "task": "accounts.tasks.delete_old_temporary_users",
        "schedule": crontab(hour=0, minute=0),  # For production: Run at midnight
    },
}

# Define periodic tasks in Celery Beat schedule
# app.conf.beat_schedule = {
#     "print-something-every-30-seconds": {
#         "task": "accounts.tasks.print_something",  # Adjust the task path here
#         "schedule": crontab(minute="*"),  # Run every minute
#     },
# }


from celery.schedules import crontab


app.conf.beat_schedule.update({
    "test-paypal-disbursement-every-minute": {
        "task": "payment_service.tasks.disburse_paypal_payments",
         "schedule": crontab(hour=0, minute=0),
        # "schedule": crontab(minute="*/1"),  # every minute
    },
})
