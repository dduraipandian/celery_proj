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

    celery.conf.update(
        task_serializer='json',
        accept_content=['json', 'pickle'],
        result_serializer='pickle',
        worker_prefetch_multiplier=1,  # to avoid early pre fetch to the queue
        task_reject_on_worker_lost=True,  # to retry if the worker is killed
        task_acks_late=True,  # to broker will only acknowledged after job completion
        task_queues=task_queues,
        broker_transport_options=broker_transport_options,
        task_default_queue='default',
        task_default_exchange_type='direct',
        task_default_routing_key='default'
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    celery.autodiscover_tasks(
        [
            'celery_proj.tasks',
        ]
    )
    return celery
