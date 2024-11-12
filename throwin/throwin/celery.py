from __future__ import absolute_import, unicode_literals

import os
from datetime import datetime
from time import sleep

from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "throwin.settings")

app = Celery("throwin")

# time zone
app.conf.enable_utc = False
app.conf.update(timezone="Asia/Dhaka")

app.config_from_object(settings, namespace="CELERY_")

app.autodiscover_tasks()
