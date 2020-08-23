from celery_proj.core.tasks import debug_task, debug_task_other

debug_task.delay()
debug_task_other.delay()