import os
from celery import Celery

# Define o módulo de configurações padrão do Django para o Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Cria a instância do aplicativo Celery
app = Celery("core")

# Carrega as configurações do Celery a partir do settings.py do Django
# O namespace='CELERY' significa que todas as chaves de configuração do Celery no settings.py devem começar com 'CELERY_'
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descobre e carrega automaticamente tarefas (tasks.py) de todos os apps instalados
app.autodiscover_tasks()
