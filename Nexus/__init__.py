# c:\Users\Hp\Desktop\Nexus\Nexus\__init__.py
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery_config import app as celery_app # Import from celery.py in the same directory

__all__ = ('celery_config',)