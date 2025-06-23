# c:\Users\Hp\Desktop\Nexus\Nexus\celery_config.py
import os
from celery import Celery # This will now correctly import from the installed library

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nexus.settings')

app = Celery('Nexus') # Or 'nexus_project_tasks', etc.

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
