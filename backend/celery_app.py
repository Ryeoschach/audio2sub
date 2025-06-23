from celery import Celery
from app.config import settings

# Initialize Celery
celery_app = Celery(
    "audio2sub_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks'] # List of modules to import when the worker starts
)

# Configuration for better stability with ML models
celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    # Increase task timeout for large files
    task_soft_time_limit=3600,  # 1 hour
    task_time_limit=3900,  # 1 hour 5 minutes
    # Prevent memory leaks with prefork pool
    worker_max_tasks_per_child=10,
    worker_prefetch_multiplier=1,
    # Use prefork pool for better concurrency support
    worker_concurrency=2,  # Limit concurrent workers for memory management
)

# If you have a lot of tasks or complex routing, you might want to use autodiscover_tasks
# celery_app.autodiscover_tasks(['app'])

if __name__ == '__main__':
    # This is for running the worker directly, e.g., `python celery_app.py worker -l info`
    # Typically, you'd run Celery using the `celery` command-line tool.
    celery_app.start()
