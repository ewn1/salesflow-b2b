import os

from celery import Celery

# Define o módulo de configurações padrão do Django para o Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Cria a instância do aplicativo Celery
app = Celery("core")

# Load Celery settings from Django's settings.py
# Namespace 'CELERY' means every Celery key in settings.py starts with 'CELERY_'
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descobre e carrega automaticamente tarefas (tasks.py) de todos os apps instalados
app.autodiscover_tasks()
