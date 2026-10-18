import os

from celery import Celery

# Set the default Django settings module for Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Create the Celery application instance
app = Celery("core")

# Load Celery settings from Django's settings.py
# Namespace 'CELERY' means every Celery key in settings.py starts with 'CELERY_'
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover and automatically load tasks (tasks.py) from all installed apps
app.autodiscover_tasks()
