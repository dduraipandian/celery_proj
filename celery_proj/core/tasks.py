import time

from celery.task import task


@task()
def debug_task():
    time.sleep(10)
    return "Task is done."


@task()
def debug_task_other():
    time.sleep(10)
    return "Task is done for other queue."
