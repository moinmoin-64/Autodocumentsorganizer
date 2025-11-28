"""
Celery Configuration
"""

from celery import Celery
import os

def make_celery(app_name=__name__):
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    celery = Celery(
        app_name,
        backend=redis_url,
        broker=redis_url
    )
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Europe/Berlin',
        enable_utc=True,
    )
    
    return celery

celery_app = make_celery('document_manager')
