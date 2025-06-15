from celery import Celery
from app.config import settings

# Initialize Celery
celery_app = Celery(
    __name__, # Using __name__ for the main module name
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks'] # List of modules to import when the worker starts
)

# Optional Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # task_track_started=True, # To report 'STARTED' state
    # worker_prefetch_multiplier=1, # Disable prefetching if tasks are long-running
    # task_acks_late=True, # Acknowledge tasks after they complete/fail
)

# If you have a lot of tasks or complex routing, you might want to use autodiscover_tasks
# celery_app.autodiscover_tasks(['app'])

if __name__ == '__main__':
    # This is for running the worker directly, e.g., `python celery_app.py worker -l info`
    # Typically, you'd run Celery using the `celery` command-line tool.
    celery_app.start()
