from __future__ import absolute_import, unicode_literals

import os
from datetime import datetime
from time import sleep

from celery import Celery
from django.conf import settings
from celery.schedules import crontab

from celery.schedules import schedule

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "throwin.settings")

app = Celery("throwin")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related config keys
#   must be prefixed with 'CELERY_'.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks in registered Django app configs.
app.autodiscover_tasks()

# Update deprecated settings
# Update deprecated settings
app.conf.update(
    broker_url="redis://redis_cache:6379",  # Replace CELERY_BROKER_URL
    result_backend="redis://redis_cache:6379",  # Replace CELERY_RESULT_BACKEND
    task_serializer="json",  # Replace CELERY_TASK_SERIALIZER
    accept_content=["json"],  # Replace CELERY_ACCEPT_CONTENT
    result_serializer="json",  # Replace CELERY_RESULT_SERIALIZER
    timezone="Asia/Dhaka",  # Replace CELERY_TIMEZONE
)


# Define periodic tasks
# app.conf.beat_schedule = {
#     "print-something-every-30-seconds": {
#         "task": "accounts.tasks.print_something",  # Adjust path to your task
#         "schedule": crontab(minute="*"),  # Runs every minute
#     },
# }
