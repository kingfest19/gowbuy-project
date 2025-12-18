"""Helper tasks for integration tests and app functionality."""
from celery import shared_task


@shared_task(name='celery.ping')
def ping():
    """Simple task that just returns 'pong'."""
    return 'pong'