# recuperacao_sn_web/celery.py

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recuperacao_sn_web.settings')

app = Celery('recuperacao_sn_web')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
