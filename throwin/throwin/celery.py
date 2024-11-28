from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

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
    timezone="Asia/Dhaka",  # Set the timezone for Celery tasks
)

# Define periodic tasks in Celery Beat schedule
app.conf.beat_schedule = {
    "print-something-every-30-seconds": {
        "task": "accounts.tasks.print_something",  # Adjust the task path here
        "schedule": crontab(minute="*"),  # Run every minute
    },
}
