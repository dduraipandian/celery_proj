from celery_proj.celery_proj import celery_app


def sample_function():
    return 1


@celery_app.task()
def sample_task(i):
    res = {'sample_function': sample_function}
    return res


@celery_app.task()
def sample_chord_aggregator(results):
    s = sum([result['sample_function']() for result in results])
    return s
