import os
from celery import Celery
from app.core.config import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('CELERY_CONFIG_MODULE', 'app.core.celery_app')

# Create the celery app
celery_app = Celery(
    'ppm_ai_first',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.tasks.ai_tasks',
        'app.tasks.status_update_tasks',
        'app.tasks.document_processing_tasks'
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task routing
    task_routes={
        'app.tasks.ai_tasks.*': {'queue': 'ai_queue'},
        'app.tasks.status_update_tasks.*': {'queue': 'status_queue'},
        'app.tasks.document_processing_tasks.*': {'queue': 'document_queue'},
    },
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIMEZONE,
    enable_utc=True,
    
    # Task execution
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'check-status-updates': {
            'task': 'app.tasks.status_update_tasks.check_due_status_updates',
            'schedule': 300.0,  # Every 5 minutes
        },
        'generate-ai-insights': {
            'task': 'app.tasks.ai_tasks.generate_project_insights',
            'schedule': 3600.0,  # Every hour
        },
        'cleanup-old-drafts': {
            'task': 'app.tasks.ai_tasks.cleanup_old_ai_drafts',
            'schedule': 86400.0,  # Daily
        },
    },
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,        # 10 minutes
    
    # Retry settings
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s',
)

# Optional: Configure Celery to use the same logging configuration
celery_app.conf.update(
    worker_hijack_root_logger=False,
    worker_log_color=True,
)

if __name__ == '__main__':
    celery_app.start()
