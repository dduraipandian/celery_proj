import os

from celery import Celery
from kombu import Exchange, Queue

JOB_QUEUE = "job_queue"
PRIORITY_JOB_QUEUE = "priority_job_queue"
DB_WRITE_QUEUE = "db_write_queue"
redis_url = os.getenv('REDISTOGO_URL', 'localhost:6379')

COMMON_ARGS = {
    "autoretry_for": (Exception,),
    "retry_kwargs": {
        'max_retries': 2
    },
    "default_retry_delay": 30  # 30 minutes
}

broker_url = "redis://" + redis_url + "/0"
result_backend = "redis://" + redis_url + "/1"

task_queues = (
    Queue(JOB_QUEUE, Exchange(JOB_QUEUE), routing_key=JOB_QUEUE),
    Queue(PRIORITY_JOB_QUEUE, Exchange(PRIORITY_JOB_QUEUE), routing_key=PRIORITY_JOB_QUEUE),
    Queue(DB_WRITE_QUEUE, Exchange(DB_WRITE_QUEUE), routing_key=DB_WRITE_QUEUE),
)

broker_transport_options = {
    'fanout_prefix': True,
    'fanout_patterns': True,
    # 1hr - redeliver task to other worker if the ack_late is responded within timeout
    'visibility_timeout': 3600
}


def make_celery(app):
    print(app.import_name)
    celery = Celery(app.import_name, backend=result_backend, broker=broker_url)

    CELERY_QUEUE_DEFAULT = 'default'
    CELERY_QUEUE_OTHER = 'other'

    celery.conf["accpet_content"] = ['application/json']
    celery.conf["task_serializer"] = 'json'
    celery.conf["result_serializer"] = 'json'
    celery.conf["task_acks_late"] = True
    celery.conf["task_default_queue"] = CELERY_QUEUE_DEFAULT
    celery.conf["worker_send_task_events"] = True
    celery.conf["worker_prefetch_multiplier"] = 1
    celery.conf["task_queues"] = (
        Queue(
            CELERY_QUEUE_DEFAULT,
            Exchange(CELERY_QUEUE_DEFAULT),
            routing_key=CELERY_QUEUE_DEFAULT,
        ),
        Queue(
            CELERY_QUEUE_OTHER,
            Exchange(CELERY_QUEUE_OTHER),
            routing_key=CELERY_QUEUE_OTHER,
        ),
    )
    celery.conf["task_routes"] = {
        'celery_proj.core.tasks.debug_task': {
            'queue': 'default',
            'routing_key': 'default',
            'exchange': 'default',
        },
        'celery_proj.core.tasks.debug_task_other': {
            'queue': 'other',
            'routing_key': 'other',
            'exchange': 'other',
        },
    }
    celery.conf["task_default_exchange_type"] = 'direct'

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    celery.autodiscover_tasks(
        [
            'celery_proj.tasks',
            'celery_proj.core.tasks'
        ]
    )
    return celery
